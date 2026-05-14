@echo off
REM ============================================================
REM  Monitor Vendas Moombox - Execucao local
REM  Coloque este arquivo na mesma pasta que monitor_vendas.py
REM ============================================================

cd /d "%~dp0"

REM Verifica se Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado. Instale em https://python.org
    pause
    exit /b 1
)

REM Instala dependencias se necessario
pip install requests beautifulsoup4 --quiet

REM Executa o monitor
python monitor_vendas.py

REM Mostra resultado (opcional - comentar em producao)
REM pause
