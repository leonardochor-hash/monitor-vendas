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

LOJAS = {
        "1": "Rio Sul",
        "3": "Barra Shopping",
        "4": "NorteShopping",
}

session = requests.Session()


def login():
        r = session.get(MOOMBOX_URL + "/user/login")
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_tag = soup.find("input", {"name": "_csrf"})
        if not csrf_tag:
                    print("ERRO: csrf nao encontrado")
                    return
                csrf = csrf_tag["value"]
    resp = session.post(MOOMBOX_URL + "/user/login", data={
                "_csrf": csrf,
                "LoginForm[username]": USUARIO,
                "LoginForm[password]": SENHA,
                "LoginForm[rememberMe]": "0",
    })
    if "logout" in resp.text.lower() or resp.url != MOOMBOX_URL + "/user/login":
                print("Login OK")
else:
        print("AVISO: Login pode ter falhado")


def buscar_totais_hora(data_str, hora):
        d = urllib.parse.quote(data_str + " - " + data_str)
    url = (MOOMBOX_URL + "/zoop/financeiro"
                      + "?TransacaoPosSearch%5Bdata%5D=" + d
                      + "&TransacaoPosSearch%5Btipo_pagamento%5D=credit"
                      + "&TransacaoPosSearch%5Bstatus%5D=succeeded"
                      + "&_togd9a55727=all")
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    totais = {lid: 0.0 for lid in LOJAS}
    loja_atual = None
    for row in soup.select("table tbody tr"):
                cols = row.find_all("td")
                if not cols:
                                continue
                            primeira = cols[0].get_text(strip=True)
        if primeira in LOJAS:
                        loja_atual = primeira
                        continue
                    if loja_atual is None or len(cols) < 4:
                                    continue
                                data_hora_txt = cols[2].get_text(strip=True)
        try:
                        dt = datetime.strptime(data_hora_txt, "%d/%m/%Y %H:%M:%S")
                        if dt.hour == hora:
                                            v = cols[3].get_text(strip=True).replace(",", ".").replace(" ", "")
                                            totais[loja_atual] += float(v)
                                    except:
            pass
    return totais


def seta(val_atual, val_ref):
        if val_ref == 0:
                    return "novo", "+100%"
    pct = ((val_atual - val_ref) / val_ref) * 100
    direcao = "sobe" if pct >= 0 else "desce"
    sinal = "+" if pct >= 0 else ""
    return direcao, sinal + "{:.1f}%".format(pct)


def formatar_brl(v):
        s = "{:,.2f}".format(v)
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + s


def enviar_whatsapp(msg):
        if not CALLMEBOT_KEY:
                    print("WhatsApp ignorado: CALLMEBOT_KEY nao configurado.")
        return
    url = "https://api.callmebot.com/whatsapp.php"
    params = {"phone": CALLMEBOT_TEL, "text": msg, "apikey": CALLMEBOT_KEY}
    try:
                requests.get(url, params=params, timeout=15)
        print("WhatsApp enviado!")
except Exception as e:
        print("Erro WhatsApp: " + str(e))


                       def main():
                               agora = datetime.now()
                               hora_atual = agora.hour
                               if hora_atual < 11 or hora_atual > 22:
                                           print("Fora do horario de funcionamento: " + str(hora_atual) + "h")
                                           return
                                       print("Iniciando coleta - " + agora.strftime("%d/%m/%Y %H:%M"))
    login()
    hoje     = agora.strftime("%d/%m/%Y")
    ontem    = (agora - timedelta(days=1)).strftime("%d/%m/%Y")
    sem_ant  = (agora - timedelta(weeks=1)).strftime("%d/%m/%Y")
    try:
                if agora.month > 1:
                                mes_ant = agora.replace(month=agora.month - 1)
else:
            mes_ant = agora.replace(year=agora.year - 1, month=12)
except ValueError:
        import calendar
        if agora.month > 1:
                        m = agora.month - 1
            y = agora.year
else:
            m = 12
            y = agora.year - 1
        last_day = calendar.monthrange(y, m)[1]
        mes_ant = agora.replace(year=y, month=m, day=min(agora.day, last_day))
    mes_ant_str = mes_ant.strftime("%d/%m/%Y")
    ano_ant = agora - timedelta(weeks=52)
    diff = agora.weekday() - ano_ant.weekday()
    ano_ant = ano_ant + timedelta(days=diff)
    ano_ant_str = ano_ant.strftime("%d/%m/%Y")
    print("Buscando dados para hora " + str(hora_atual) + "h...")
    atual = buscar_totais_hora(hoje,        hora_atual)
    d_ont = buscar_totais_hora(ontem,       hora_atual)
    d_sem = buscar_totais_hora(sem_ant,     hora_atual)
    d_mes = buscar_totais_hora(mes_ant_str, hora_atual)
    d_ano = buscar_totais_hora(ano_ant_str, hora_atual)
    linhas = [
                "Vendas Cartao Credito - {:02d}h".format(hora_atual),
                "Data: " + hoje,
                "-------------------------",
    ]
    total_geral = 0.0
    for lid, nome in LOJAS.items():
                v = atual.get(lid, 0.0)
        total_geral += v
        e1, p1 = seta(v, d_ont.get(lid, 0.0))
        e2, p2 = seta(v, d_sem.get(lid, 0.0))
        e3, p3 = seta(v, d_mes.get(lid, 0.0))
        e4, p4 = seta(v, d_ano.get(lid, 0.0))
        linhas.append("*" + nome + "*:  " + formatar_brl(v))
        linhas.append("  " + e1 + " vs ontem ("   + ontem       + "): " + formatar_brl(d_ont.get(lid, 0.0)) + " (" + p1 + ")")
        linhas.append("  " + e2 + " vs sem.ant (" + sem_ant     + "): " + formatar_brl(d_sem.get(lid, 0.0)) + " (" + p2 + ")")
        linhas.append("  " + e3 + " vs mes ant (" + mes_ant_str + "): " + formatar_brl(d_mes.get(lid, 0.0)) + " (" + p3 + ")")
        linhas.append("  " + e4 + " vs ano ant (" + ano_ant_str + "): " + formatar_brl(d_ano.get(lid, 0.0)) + " (" + p4 + ")")
        linhas.append("")
    linhas.append("-----------------------------")
    linhas.append("TOTAL GERAL: " + formatar_brl(total_geral))
    mensagem = "\n".join(linhas)
    print("=" * 40)
    print(mensagem)
    print("=" * 40)
    enviar_whatsapp(mensagem)


if __name__ == "__main__":
        main()
