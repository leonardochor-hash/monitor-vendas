# Monitor de Vendas Cartão de Crédito

Monitor automático de vendas por cartão de crédito das lojas **Moombox** (Rio Sul, Barra Shopping, NorteShopping), com envio via WhatsApp (CallMeBot).

---

## 🔗 Links Úteis

| Recurso | URL |
|---|---|
| **Repositório** | https://github.com/leonardochor-hash/monitor-vendas |
| **GitHub Actions** | https://github.com/leonardochor-hash/monitor-vendas/actions/workflows/monitor.yml |
| **Console PythonAnywhere** | https://www.pythonanywhere.com/user/leonardochor/consoles/46753769/ |

---

## ▶️ Como Rodar Manualmente

1. Acesse: https://github.com/leonardochor-hash/monitor-vendas/actions/workflows/monitor.yml
2. Clique em **"Run workflow"** (botão no canto superior direito)
3. Clique no **"Run workflow"** verde
4. Aguarde ~15s e abra o run → job `monitorar` → step **"Executar monitoramento"**

---

## ⏰ Agendamento Automático

Roda automaticamente **toda hora, das 11h às 22h (horário de Brasília)**.

| UTC | Brasília |
|---|---|
| 14h | 11h |
| 15h | 12h |
| 16h | 13h |
| 17h | 14h |
| 18h | 15h |
| 19h | 16h |
| 20h | 17h |
| 21h | 18h |
| 22h | 19h |
| 23h | 20h |
| 00h | 21h |
| 01h | 22h |

---

## 🏪 Lojas Monitoradas

| ID | Loja |
|---|---|
| 1 | Rio Sul |
| 3 | Barra Shopping |
| 4 | NorteShopping |

---

## 📊 Formato do Report

```
Vendas Cartao Credito - 22h
Data: 13/05/2026
-------------------------
*Barra Shopping*:  R$ X.XXX,XX
  sobe vs ontem (12/05/2026): R$ X.XXX,XX (+X%)
  sobe vs sem.ant (06/05/2026): R$ X.XXX,XX (+X%)
  sobe vs mes ant (13/04/2026): R$ X.XXX,XX (+X%)
  sobe vs ano ant (14/05/2025): R$ X.XXX,XX (+X%)

*Rio Sul*:  R$ X.XXX,XX
  ...

*NorteShopping*:  R$ X.XXX,XX
  ...

-----------------------------
TOTAL GERAL: R$ X.XXX,XX
```

---

## ⚠️ Pendências

1. **Login Moombox falhando** — verificar se as credenciais `moombox`/`admin2020b` em `monitor_vendas.py` ainda são válidas em https://expositores.moombox.com.br
2. **WhatsApp não enviando** — configurar o secret `CALLMEBOT_KEY` em: https://github.com/leonardochor-hash/monitor-vendas/settings/secrets/actions

---

## 🔧 Configuração

### Secrets necessários (GitHub Actions)

| Secret | Descrição |
|---|---|
| `CALLMEBOT_KEY` | Chave API do CallMeBot para envio via WhatsApp |

Para adicionar: **Settings → Secrets and variables → Actions → New repository secret**

### Dependências Python

```bash
pip install requests beautifulsoup4
```

---

## 📝 Contexto para retomar com Claude

Cole este README numa nova conversa com Claude e diga:
> "Quero continuar o projeto monitor-vendas. Aqui está o README com o contexto."

Ele conseguirá retomar de onde paramos!
