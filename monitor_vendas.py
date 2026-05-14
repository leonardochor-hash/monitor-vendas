import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import urllib.parse
import os

MOOMBOX_URL   = "https://expositores.moombox.com.br"
USUARIO       = "moombox"
SENHA         = "admin2020b"
CALLMEBOT_TEL = "5521992971444"
CALLMEBOT_KEY = os.environ.get("CALLMEBOT_KEY", "")
PROXY_URL     = os.environ.get("PROXY_URL", "")
HORA_SIMULADA = os.environ.get("HORA_SIMULADA", "")
DATA_SIMULADA = os.environ.get("DATA_SIMULADA", "")

LOJAS = {
    "1": "Rio Sul",
    "3": "Barra Shopping",
    "4": "NorteShopping",
}

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
    })
    if PROXY_URL:
        s.proxies = {"http": PROXY_URL, "https": PROXY_URL}
        print(f"Usando proxy: {PROXY_URL}")
    return s

session = make_session()

def login():
    try:
        r = session.get(MOOMBOX_URL + "/user/login", timeout=30)
    except Exception as e:
        print(f"ERRO ao acessar login: {e}")
        return False
    soup = BeautifulSoup(r.text, "html.parser")
    csrf_tag = soup.find("input", {"name": "_csrf"})
    if not csrf_tag:
        print("ERRO: csrf nao encontrado na pagina de login")
        return False
    csrf = csrf_tag["value"]
    resp = session.post(MOOMBOX_URL + "/user/login", data={
        "_csrf": csrf,
        "LoginForm[username]": USUARIO,
        "LoginForm[password]": SENHA,
        "LoginForm[rememberMe]": "0",
    }, timeout=30)
    if "logout" in resp.text.lower():
        print("Login OK")
        return True
    else:
        print("AVISO: Login pode ter falhado")
        return False

def buscar_totais_dia(data_str):
    # Retorna dict {loja_id: total_dia}
    d = urllib.parse.quote(data_str + " - " + data_str)
    url = (MOOMBOX_URL + "/zoop/financeiro"
           + "?TransacaoPosSearch%5Bdata%5D=" + d
           + "&TransacaoPosSearch%5Btipo_pagamento%5D=credit"
           + "&TransacaoPosSearch%5Bstatus%5D=succeeded"
           + "&_togd9a55727=all")
    try:
        r = session.get(url, timeout=30)
    except Exception as e:
        print(f"ERRO ao buscar financeiro: {e}")
        return {lid: 0.0 for lid in LOJAS}
    soup = BeautifulSoup(r.text, "html.parser")
    totais = {lid: 0.0 for lid in LOJAS}
    loja_atual = None
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if not cols:
            continue
        if len(cols) == 17:
            c1 = cols[1].get_text(strip=True)
            if c1 in LOJAS:
                loja_atual = c1
                v_txt = cols[4].get_text(strip=True).replace(".", "").replace(",", ".").replace(" ", "")
                try:
                    totais[loja_atual] += float(v_txt)
                except:
                    pass
            continue
        if len(cols) == 16 and loja_atual:
            v_txt = cols[3].get_text(strip=True).replace(".", "").replace(",", ".").replace(" ", "")
            try:
                totais[loja_atual] += float(v_txt)
            except:
                pass
    return totais

def buscar_totais_hora(data_str, hora):
    # Retorna dict {loja_id: total_da_hora}
    d = urllib.parse.quote(data_str + " - " + data_str)
    url = (MOOMBOX_URL + "/zoop/financeiro"
           + "?TransacaoPosSearch%5Bdata%5D=" + d
           + "&TransacaoPosSearch%5Btipo_pagamento%5D=credit"
           + "&TransacaoPosSearch%5Bstatus%5D=succeeded"
           + "&_togd9a55727=all")
    try:
        r = session.get(url, timeout=30)
    except Exception as e:
        print(f"ERRO ao buscar financeiro hora: {e}")
        return {lid: 0.0 for lid in LOJAS}
    soup = BeautifulSoup(r.text, "html.parser")
    totais = {lid: 0.0 for lid in LOJAS}
    loja_atual = None
    for row in soup.select("table tbody tr"):
        cols = row.find_all("td")
        if not cols:
            continue
        if len(cols) == 17:
            c1 = cols[1].get_text(strip=True)
            if c1 in LOJAS:
                loja_atual = c1
                dh = cols[3].get_text(strip=True)
                try:
                    dt = datetime.strptime(dh, "%d/%m/%Y %H:%M:%S")
                    if dt.hour == hora:
                        v_txt = cols[4].get_text(strip=True).replace(".", "").replace(",", ".").replace(" ", "")
                        totais[loja_atual] += float(v_txt)
                except:
                    pass
            continue
        if len(cols) == 16 and loja_atual:
            dh = cols[2].get_text(strip=True)
            try:
                dt = datetime.strptime(dh, "%d/%m/%Y %H:%M:%S")
                if dt.hour == hora:
                    v_txt = cols[3].get_text(strip=True).replace(".", "").replace(",", ".").replace(" ", "")
                    totais[loja_atual] += float(v_txt)
            except:
                pass
    return totais

def seta(atual, ref):
    if ref == 0:
        return "novo"
    diff = atual - ref
    pct = (diff / ref * 100) if ref != 0 else 0
    sinal = "sobe" if diff >= 0 else "cai"
    return f"{sinal} vs {{ref_label}}: R$ {abs(diff):,.2f} ({abs(pct):.1f}%)".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def delta_str(atual, ref, label, ref_data_str):
    if ref == 0:
        return f"  sem dado vs {label} ({ref_data_str})"
    diff = atual - ref
    pct  = diff / ref * 100
    sinal = "sobe" if diff >= 0 else "cai"
    diff_fmt = formatar_brl(abs(diff))
    return f"  {sinal} vs {label} ({ref_data_str}): {diff_fmt} ({abs(pct):.1f}%)"

def enviar_whatsapp(mensagem):
    if not CALLMEBOT_KEY:
        print("WhatsApp ignorado: CALLMEBOT_KEY nao configurado.")
        return
    try:
        msg_enc = urllib.parse.quote(mensagem)
        url = f"https://api.callmebot.com/whatsapp.php?phone={CALLMEBOT_TEL}&text={msg_enc}&apikey={CALLMEBOT_KEY}"
        r = requests.get(url, timeout=20)
        print(f"WhatsApp enviado: {r.status_code}")
    except Exception as e:
        print(f"Erro WhatsApp: {e}")

def main():
    agora_utc = datetime.utcnow()
    # Brasilia = UTC-3
    agora_br  = agora_utc - timedelta(hours=3)
    hora_br   = agora_br.hour
    if DATA_SIMULADA:
        try:
            agora_br = datetime.strptime(DATA_SIMULADA, "%d/%m/%Y").replace(
                hour=int(HORA_SIMULADA) if HORA_SIMULADA else agora_br.hour,
                minute=0, second=0)
            print(f"[SIMULACAO] Data/hora: {agora_br.strftime('%d/%m/%Y %H:%M')}")
            hora_br = agora_br.hour
        except Exception as e:
            print(f"Erro simulacao: {e}")
    elif HORA_SIMULADA:
        hora_br = int(HORA_SIMULADA)
        print(f"[SIMULACAO] Hora forcada: {hora_br}h")


    HORA_INICIO = 11
    HORA_FIM    = 22

    if hora_br < HORA_INICIO or hora_br > HORA_FIM:
        print(f"Fora do horario de funcionamento: {hora_br}h")
        return

    print(f"Horario Brasilia: {agora_br.strftime('%d/%m/%Y %H:%M')}")

    if not login():
        print("Abortando: falha no login")
        return

    hoje      = agora_br.strftime("%d/%m/%Y")
    ontem     = (agora_br - timedelta(days=1)).strftime("%d/%m/%Y")
    sem_ant   = (agora_br - timedelta(days=7)).strftime("%d/%m/%Y")
    mes_ant   = (agora_br - timedelta(days=30)).strftime("%d/%m/%Y")
    ano_ant   = (agora_br - timedelta(days=365)).strftime("%d/%m/%Y")

    print(f"Buscando dados de hoje ({hoje})...")
    totais_hoje = buscar_totais_hora(hoje, hora_br)
    print(f"  Totais hora {hora_br}h: {totais_hoje}")

    totais_ontem   = buscar_totais_dia(ontem)
    totais_sem_ant = buscar_totais_dia(sem_ant)
    totais_mes_ant = buscar_totais_dia(mes_ant)
    totais_ano_ant = buscar_totais_dia(ano_ant)

    linhas = []
    linhas.append(f"Vendas Cartao Credito - {hora_br}h")
    linhas.append(f"Data: {hoje}")
    linhas.append("-------------------------")

    total_geral = 0.0
    for lid, lnome in LOJAS.items():
        v = totais_hoje.get(lid, 0.0)
        total_geral += v
        linhas.append(f"*{lnome}*:  {formatar_brl(v)}")
        linhas.append(delta_str(v, totais_ontem.get(lid, 0.0),  "ontem",   ontem))
        linhas.append(delta_str(v, totais_sem_ant.get(lid, 0.0),"sem.ant", sem_ant))
        linhas.append(delta_str(v, totais_mes_ant.get(lid, 0.0),"mes ant", mes_ant))
        linhas.append(delta_str(v, totais_ano_ant.get(lid, 0.0),"ano ant", ano_ant))

    linhas.append("-----------------------------")
    linhas.append("TOTAL GERAL: " + formatar_brl(total_geral))
    mensagem = "\n".join(linhas)
    print(mensagem)
    enviar_whatsapp(mensagem)

if __name__ == "__main__":
    main()
