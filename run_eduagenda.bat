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

:: Tenta usar o venv da versao mais recente instalada
set "PY=python"
for /d %%V in (versions\v*) do (
    if exist "%%V\venv\Scripts\python.exe" (
        set "PY=%%V\venv\Scripts\python.exe"
    )
)

%PY% manager\manager.py
pause
