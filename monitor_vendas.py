import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os

MOOMBOX_URL   = "https://expositores.moombox.com.br"
USUARIO       = "moombox"
SENHA         = "admin2020b"
CALLMEBOT_TEL = "5521992971444"
CALLMEBOT_KEY = os.environ.get("CALLMEBOT_KEY", "")
HORA_SIMULADA = os.environ.get("HORA_SIMULADA", "")
DATA_SIMULADA = os.environ.get("DATA_SIMULADA", "")

LOJAS = {"1": "Rio Sul", "3": "Barra Shopping", "4": "NorteShopping"}

def make_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    return s

session = make_session()

def login():
    try:
        r = session.get(MOOMBOX_URL + "/user/login", timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_tag = soup.find("input", {"name": "_csrf"})
        if not csrf_tag:
            print("ERRO: csrf nao encontrado na pagina de login")
            return False
        csrf = csrf_tag["value"]
        resp = session.post(MOOMBOX_URL + "/user/login", data={
            "_csrf": csrf,
            "login-form[login]": USUARIO,
            "login-form[password]": SENHA,
            "login-form[rememberMe]": "0",
        }, timeout=30)
        if "logout" in resp.text.lower():
            print("Login OK")
            return True
        else:
            print("AVISO: Login pode ter falhado")
            return False
    except Exception as e:
        print(f"ERRO ao acessar login: {e}")
        return False

def buscar_zoop(data_str, hora_max=None):
    """
    Busca transacoes Zoop do dia data_str (DD/MM/YYYY).
    Se hora_max for int, filtra apenas transacoes com hora < hora_max (ate hora_max-1:59).
    Retorna dict {loja_id: total_valor_operacao}
    Status: succeeded. Todos os tipos de pagamento (credit, debit, pix).
    """
    data_enc = data_str + " - " + data_str
    params = {
        "TransacaoPosSearch[data]": data_enc,
        "TransacaoPosSearch[status]": "succeeded",
        "TransacaoPosSearch[authorization_code]": "",
        "TransacaoPosSearch[tipo_pagamento]": "",
        "TransacaoPosSearch[entry_mode]": "",
        "TransacaoPosSearch[id_zoop]": "",
    }
    try:
        r = session.get(MOOMBOX_URL + "/zoop/financeiro", params=params, timeout=30)
        soup = BeautifulSoup(r.text, "html.parser")
        totais = {}
        current_loja = None
        for row in soup.select("table tbody tr"):
            cells = row.find_all("td")
            if len(cells) == 17:
                # Primeira linha de cada grupo de loja
                current_loja = cells[1].get_text(strip=True)
                data_hora = cells[3].get_text(strip=True)  # "13/05/2026 HH:MM:SS"
                valor_op = cells[5].get_text(strip=True)
            elif len(cells) == 16:
                if cells[1].get_text(strip=True) == "Total":
                    continue
                data_hora = cells[2].get_text(strip=True)
                valor_op = cells[4].get_text(strip=True)
            else:
                continue
            if current_loja not in LOJAS:
                continue
            # Filtrar por hora se necessario
            if hora_max is not None:
                try:
                    hora_transacao = int(data_hora.split(" ")[1].split(":")[0])
                    if hora_transacao >= hora_max:
                        continue
                except:
                    pass
            try:
                valor = float(valor_op.replace(",", "."))
                totais[current_loja] = totais.get(current_loja, 0.0) + valor
            except:
                pass
        return totais
    except Exception as e:
        print(f"ERRO ao buscar Zoop {data_str}: {e}")
        return {}

def formatar_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def delta_str(atual, referencia, data_ref_label):
    if referencia == 0:
        return f"  sem dado vs {data_ref_label}"
    diff = atual - referencia
    pct = diff / referencia * 100
    sinal = "+" if diff >= 0 else ""
    return f"  vs {data_ref_label}: {formatar_brl(referencia)} ({sinal}{pct:.1f}%)"

def enviar_whatsapp(msg):
    if not CALLMEBOT_KEY:
        print("WhatsApp ignorado: CALLMEBOT_KEY nao configurado.")
        return
    import urllib.parse
    url = (f"https://api.callmebot.com/whatsapp.php"
           f"?phone={CALLMEBOT_TEL}&text={urllib.parse.quote(msg)}&apikey={CALLMEBOT_KEY}")
    try:
        r = requests.get(url, timeout=15)
        print(f"WhatsApp: {r.status_code}")
    except Exception as e:
        print(f"Erro WhatsApp: {e}")

def main():
    agora_utc = datetime.utcnow()
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

    if hora_br < 11 or hora_br > 22:
        print(f"Fora do horario de funcionamento: {hora_br}h")
        return

    hoje     = agora_br.strftime("%d/%m/%Y")
    ontem    = (agora_br - timedelta(days=1)).strftime("%d/%m/%Y")
    sem_ant  = (agora_br - timedelta(days=7)).strftime("%d/%m/%Y")
    mes_ant  = (agora_br - timedelta(days=28)).strftime("%d/%m/%Y")
    ano_ant  = (agora_br - timedelta(days=364)).strftime("%d/%m/%Y")

    print(f"Horario Brasilia: {agora_br.strftime('%d/%m/%Y %H:%M')}")

    if not login():
        print("Abortando: falha no login")
        return

    # Buscar totais ÃÂÃÂ¢ÃÂÃÂÃÂÃÂ hoje filtrado por hora, demais dias totais
    totais_hoje    = buscar_zoop(hoje,    hora_max=hora_br)
    totais_ontem   = buscar_zoop(ontem,   hora_max=hora_br)
    totais_sem_ant = buscar_zoop(sem_ant, hora_max=hora_br)
    totais_mes_ant = buscar_zoop(mes_ant, hora_max=hora_br)
    totais_ano_ant = buscar_zoop(ano_ant, hora_max=hora_br)

    linhas = [
        f"Vendas Cartao Credito - {hora_br}h",
        f"Data: {hoje}",
        "-------------------------",
    ]
    total_geral = 0.0
    for loja_id, loja_nome in LOJAS.items():
        v_hoje    = totais_hoje.get(loja_id, 0.0)
        v_ontem   = totais_ontem.get(loja_id, 0.0)
        v_sem     = totais_sem_ant.get(loja_id, 0.0)
        v_mes     = totais_mes_ant.get(loja_id, 0.0)
        v_ano     = totais_ano_ant.get(loja_id, 0.0)
        total_geral += v_hoje
        linhas.append(f"*{loja_nome}*:  {formatar_brl(v_hoje)}")
        linhas.append(delta_str(v_hoje, v_ontem,   f"ontem ({ontem})"))
        linhas.append(delta_str(v_hoje, v_sem,     f"sem.ant ({sem_ant})"))
        linhas.append(delta_str(v_hoje, v_mes,     f"mes ant ({mes_ant})"))
        linhas.append(delta_str(v_hoje, v_ano,     f"ano ant ({ano_ant})"))

    linhas.append("-----------------------------")
    linhas.append(f"TOTAL GERAL: {formatar_brl(total_geral)}")

    msg = "\n".join(linhas)
    print(msg)
    enviar_whatsapp(msg)

if __name__ == "__main__":
    main()
