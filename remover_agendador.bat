@echo off
REM Remove todas as tarefas do Monitor Vendas do Agendador
echo Removendo tarefas MonitorVendasMoombox...
for %%H in (11 12 13 14 15 16 17 18 19 20 21 22) do (
    schtasks /delete /tn "MonitorVendasMoombox_%%H" /f >nul 2>&1
)
echo Tarefas removidas com sucesso.
pause
