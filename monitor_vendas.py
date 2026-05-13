import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import urllib.parse
import os


MOOMBOX_URL   = "https://expositores.moombox.com.br"
USUARIO       = "moombox"
SENHA         = "admin2020b"
CALLMEBOT_TEL = "5521992971444"
CALLMEBOT_KEY = os.environ.get("CALLMEBOT_KEY", "SUA_API_KEY_AQUI")


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
    session.post(MOOMBOX_URL + "/user/login", data={
        "_csrf": csrf,
        "LoginForm[username]": USUARIO,
        "LoginForm[password]": SENHA,
        "LoginForm[rememberMe]": "0",
    })
    print("Login realizado")

