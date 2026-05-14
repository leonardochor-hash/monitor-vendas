import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MOOMBOX_URL = "https://expositores.moombox.com.br"
USUARIO = "moombox"
SENHA = "admin2020b"
CALLMEBOT_TEL = "5521992971444"
CALLMEBOT_KEY = os.environ.get("CALLMEBOT_KEY", "")
HORA_SIMULADA = os.environ.get("HORA_SIMULADA", "")
DATA_SIMULADA = os.environ.get("DATA_SIMULADA", "")

EMAIL_REMETENTE = os.environ.get("EMAIL_REMETENTE", "cap00leonardo@gmail.com")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO", "leonardochor@gmail.com")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

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
                current_loja = cells[1].get_text(strip=True)
                data_hora = cells[3].get_text(strip=True)
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
        print(f"WhatsApp enviado: {r.status_code}")
    except Exception as e:
        print(f"ERRO ao enviar WhatsApp: {e}")

def enviar_email(assunto, corpo_texto, corpo_html=None):
    if not GMAIL_APP_PASSWORD:
        print("Email ignorado: GMAIL_APP_PASSWORD nao configurado.")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = EMAIL_REMETENTE
        msg["To"] = EMAIL_DESTINATARIO
        part_texto = MIMEText(corpo_texto, "plain", "utf-8")
        msg.attach(part_texto)
        if corpo_html:
            part_html = MIMEText(corpo_html, "html", "utf-8")
            msg.attach(part_html)
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(EMAIL_REMETENTE, GMAIL_APP_PASSWORD)
            smtp.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        print(f"Email enviado para {EMAIL_DESTINATARIO}")
    except Exception as e:
        print(f"ERRO ao enviar email: {e}")

def montar_html(linhas_texto):
    """Converte o relatorio texto em HTML formatado para email."""
    import html as html_lib
    html = """<html><body style="font-family:monospace;font-size:14px;">"""
    html += "<pre style='background:#f8f8f8;padding:16px;border-radius:6px;'>"
    html += html_lib.escape(linhas_texto)
    html += "</pre></body></html>"
    return html

def normalizar_hora_str(hora_str):
    """Converte '20' ou '20:00' para '20:00'."""
    hora_str = hora_str.strip()
    if ":" not in hora_str:
        return hora_str + ":00"
    return hora_str

def main():
    if DATA_SIMULADA:
        hora_str = normalizar_hora_str(HORA_SIMULADA) if HORA_SIMULADA else "20:00"
        agora_br = datetime.strptime(DATA_SIMULADA + " " + hora_str, "%d/%m/%Y %H:%M")
    else:
        import pytz
        tz_br = pytz.timezone("America/Sao_Paulo")
        agora_br = datetime.now(tz_br).replace(tzinfo=None)

    hora_br = agora_br.hour

    if not (11 <= hora_br <= 22):
        print(f"Fora do horario de operacao ({hora_br}h). Nenhum relatorio enviado.")
        return

    hoje    = agora_br.strftime("%d/%m/%Y")
    ontem   = (agora_br - timedelta(days=1)).strftime("%d/%m/%Y")
    sem_ant = (agora_br - timedelta(days=7)).strftime("%d/%m/%Y")
    mes_ant = (agora_br - timedelta(days=28)).strftime("%d/%m/%Y")
    ano_ant = (agora_br - timedelta(days=364)).strftime("%d/%m/%Y")

    print(f"Iniciando relatorio: {hoje} {hora_br:02d}:xx (ate {hora_br-1}:59)")
    print(f"Comparacoes: ontem={ontem} | sem_ant={sem_ant} | mes_ant={mes_ant} | ano_ant={ano_ant}")

    if not login():
        print("ERRO: Login falhou. Abortando.")
        return

    totais_hoje    = buscar_zoop(hoje,    hora_max=hora_br)
    totais_ontem   = buscar_zoop(ontem,   hora_max=hora_br)
    totais_sem_ant = buscar_zoop(sem_ant, hora_max=hora_br)
    totais_mes_ant = buscar_zoop(mes_ant, hora_max=hora_br)
    totais_ano_ant = buscar_zoop(ano_ant, hora_max=hora_br)

    hora_label = f"{hora_br-1:02d}:59"
    linhas = [f"Moombox Vendas - {hoje} ate {hora_label}", "=" * 45]

    for loja_id, loja_nome in LOJAS.items():
        v_hoje    = totais_hoje.get(loja_id, 0.0)
        v_ontem   = totais_ontem.get(loja_id, 0.0)
        v_sem_ant = totais_sem_ant.get(loja_id, 0.0)
        v_mes_ant = totais_mes_ant.get(loja_id, 0.0)
        v_ano_ant = totais_ano_ant.get(loja_id, 0.0)

        linhas.append(f"{loja_nome}: {formatar_brl(v_hoje)}")
        linhas.append(delta_str(v_hoje, v_ontem,   f"ontem   ({ontem})"))
        linhas.append(delta_str(v_hoje, v_sem_ant, f"sem.ant ({sem_ant})"))
        linhas.append(delta_str(v_hoje, v_mes_ant, f"mes ant ({mes_ant})"))
        linhas.append(delta_str(v_hoje, v_ano_ant, f"ano ant ({ano_ant})"))
        linhas.append("")

    total_hoje    = sum(totais_hoje.values())
    total_ontem   = sum(totais_ontem.values())
    total_sem_ant = sum(totais_sem_ant.values())
    total_mes_ant = sum(totais_mes_ant.values())
    total_ano_ant = sum(totais_ano_ant.values())

    linhas.append("=" * 45)
    linhas.append(f"TOTAL: {formatar_brl(total_hoje)}")
    linhas.append(delta_str(total_hoje, total_ontem,   f"ontem   ({ontem})"))
    linhas.append(delta_str(total_hoje, total_sem_ant, f"sem.ant ({sem_ant})"))
    linhas.append(delta_str(total_hoje, total_mes_ant, f"mes ant ({mes_ant})"))
    linhas.append(delta_str(total_hoje, total_ano_ant, f"ano ant ({ano_ant})"))

    relatorio = "\n".join(linhas)
    print(relatorio)

    assunto = f"Moombox Vendas {hoje} ate {hora_label}"
    corpo_html = montar_html(relatorio)

    enviar_email(assunto, relatorio, corpo_html)
    enviar_whatsapp(relatorio)

if __name__ == "__main__":
    main()
