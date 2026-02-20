@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   EduAgenda - Super Instalador v2.0
echo   Arquitetura: Software com Vida
echo ==========================================

:: 1. Bootstrap de Dependencias (Python e Git)
echo [*] Garantindo Python e Git no sistema...
powershell -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"
if errorlevel 1 goto :bootstrap_fail

:: Recarregar PATH
for /f "tokens=*" %%a in ('powershell -command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%a"

:: 2. Definir Estrutura Raiz
set "ROOT=C:\EduAgenda"
echo [*] Preparando estrutura em: %ROOT%

if not exist "%ROOT%" mkdir "%ROOT%"
if not exist "%ROOT%\versions" mkdir "%ROOT%\versions"
if not exist "%ROOT%\shared" mkdir "%ROOT%\shared"
if not exist "%ROOT%\shared\data" mkdir "%ROOT%\shared\data"
if not exist "%ROOT%\shared\logs" mkdir "%ROOT%\shared\logs"
if not exist "%ROOT%\manager" mkdir "%ROOT%\manager"

:: 3. Sincronizacao da Versao Inicial (v1.2.0)
set "V_TAG=v1.2.0"
set "INIT_V_PATH=%ROOT%\versions\%V_TAG%"

echo [*] Instalando Versao Base (%V_TAG%)...
if not exist "%INIT_V_PATH%" (
    mkdir "%INIT_V_PATH%"
    cd /d "%INIT_V_PATH%"
    git clone https://github.com/vinniciusbrun/EduAgenda.git .
) else (
    echo [i] Versao %V_TAG% ja existe.
    cd /d "%INIT_V_PATH%"
    git fetch --all
    git reset --hard origin/master
)

:: 4. Migrar/Configurar Orquestrador
echo [*] Configurando Orquestrador...
copy /y "%INIT_V_PATH%\manager\manager.py" "%ROOT%\manager\manager.py"
copy /y "%INIT_V_PATH%\run_eduagenda.bat" "%ROOT%\run_eduagenda.bat"

:: 5. Setup do Ambiente Virtual (venv) na versao
cd /d "%INIT_V_PATH%"
if not exist "venv\Scripts\activate.bat" (
    echo [*] Criando ambiente virtual para %V_TAG%...
    python -m venv venv
)

echo [*] Instalando dependencias...
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_fail

:: 6. Inicializacao do Banco de Dados
echo [*] Inicializando banco de dados compartilhado...
set "EDU_DATA_PATH=%ROOT%\shared\data"
python init_db.py

echo.
echo ==========================================
echo   Instalacao Concluida! 
echo   Use o 'run_eduagenda.bat' na raiz de 
echo   C:\EduAgenda para iniciar o sistema.
echo ==========================================
echo.

pause
exit /b

:bootstrap_fail
echo [!] Erro no Bootstrap.
pause
exit /b

:pip_fail
echo [!] Erro ao instalar dependencias.
pause
exit /b
