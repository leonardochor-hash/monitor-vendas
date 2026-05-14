@echo off
REM ============================================================
REM  Instala o Monitor Vendas no Agendador de Tarefas Windows
REM  EXECUTE COMO ADMINISTRADOR (clique direito > Executar como admin)
REM ============================================================

cd /d "%~dp0"

echo.
echo === Instalando Monitor Vendas no Agendador de Tarefas ===
echo.

REM Define o caminho do bat e do Python
set "SCRIPT_BAT=%~dp0rodar_local.bat"

REM Verifica se o rodar_local.bat existe
if not exist "%SCRIPT_BAT%" (
    echo ERRO: rodar_local.bat nao encontrado em %~dp0
    echo Certifique-se de que ambos os arquivos estao na mesma pasta.
    pause
    exit /b 1
)

REM Remove tarefa anterior se existir
schtasks /delete /tn "MonitorVendasMoombox" /f >nul 2>&1

REM Cria a tarefa agendada para rodar de hora em hora, das 11h as 22h
REM (uma entrada por hora para controle fino)
for %%H in (11 12 13 14 15 16 17 18 19 20 21 22) do (
    schtasks /create /tn "MonitorVendasMoombox_%%H" /tr ""%SCRIPT_BAT%"" /sc daily /st %%H:00 /f >nul
    echo   Agendado: %%Hh
)

echo.
echo === Instalacao concluida! ===
echo O monitor rodara todos os dias de 11h as 22h.
echo.
echo Para verificar: Abra o Agendador de Tarefas e procure por "MonitorVendasMoombox"
echo Para remover:   Execute remover_agendador.bat
echo.
pause
