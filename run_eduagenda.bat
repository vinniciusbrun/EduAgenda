@echo off
setlocal
echo ==========================================
echo   EduAgenda - Iniciando Via Orquestrador
echo ==========================================

:: Verifica se o manager existe
if not exist "manager\manager.py" (
    echo [!] Erro: Manager nao encontrado. Execute o instalador primeiro.
    pause
    exit /b
)

:: Tenta usar o venv da v1.2.0 para rodar o manager ou o python global
if exist "versions\v1.2.0\venv\Scripts\python.exe" (
    set PY="versions\v1.2.0\venv\Scripts\python.exe"
) else (
    set PY=python
)

%PY% manager\manager.py
pause
