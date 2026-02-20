@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   EduAgenda - Super Instalador v2.1
echo   Arquitetura: Software com Vida
echo ==========================================

:: 1. Detecção de Versão Dinâmica
if exist "%~dp0..\version.json" (
    for /f "tokens=2 delims=:," %%a in ('findstr "version" "%~dp0..\version.json"') do (
        set "V_TAG=%%a"
        set "V_TAG=!V_TAG:"=!"
        set "V_TAG=!V_TAG: =!"
    )
    set "V_TAG=v!V_TAG!"
    echo [i] Versao Detectada: !V_TAG!
) else (
    echo [i] Arquivo version.json nao encontrado. Assumindo primeira instalacao limpa ^(main^).
    set "V_TAG=main"
)

:: 2. Bootstrap de Dependencias (Python e Git)
echo [*] Garantindo Python e Git no sistema...
powershell -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"
if errorlevel 1 goto :bootstrap_fail

:: Recarregar PATH
for /f "tokens=*" %%a in ('powershell -command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%a"

:: 3. Definir Estrutura Raiz (Pergunta ao usuario)
set "DEFAULT_ROOT=C:\EduAgenda"
echo.
echo Onde deseja instalar o EduAgenda?
echo [1] Padrao (%DEFAULT_ROOT%)
echo [2] Pasta Atual (%CD%\..)
set /p "CHOICE=Opcao (1/2) [1]: "

if "%CHOICE%"=="2" (
    set "ROOT=%CD%\.."
) else (
    set "ROOT=%DEFAULT_ROOT%"
)

echo [*] Preparando estrutura em: %ROOT%

if not exist "%ROOT%" mkdir "%ROOT%"
if not exist "%ROOT%\versions" mkdir "%ROOT%\versions"
if not exist "%ROOT%\shared" mkdir "%ROOT%\shared"
if not exist "%ROOT%\shared\data" mkdir "%ROOT%\shared\data"
if not exist "%ROOT%\shared\logs" mkdir "%ROOT%\shared\logs"
if not exist "%ROOT%\manager" mkdir "%ROOT%\manager"

:: 4. Sincronizacao da Versao
set "INIT_V_PATH=%ROOT%\versions\%V_TAG%"

echo [*] Instalando/Atualizando Versao %V_TAG%...
if not exist "%INIT_V_PATH%" mkdir "%INIT_V_PATH%"

:: Se estivermos rodando de dentro de um repo, copiamos em vez de clonar se for a mesma versao
if exist "%~dp0..\app.py" (
    echo [*] Copiando arquivos locais para a pasta da versao...
    xcopy /s /e /y /i "%~dp0..\\*" "%INIT_V_PATH%\\"
) else (
    echo [*] Clonando versao do GitHub...
    cd /d "%INIT_V_PATH%"
    git clone https://github.com/vinniciusbrun/EduAgenda.git .
)

:: Re-detecção de versão caso tenha sido uma instalação limpa (fallback para 'main')
if "%V_TAG%"=="main" (
    if exist "%INIT_V_PATH%\version.json" (
        for /f "tokens=2 delims=:," %%a in ('findstr "version" "%INIT_V_PATH%\version.json"') do (
            set "NEW_V=%%a"
            set "NEW_V=!NEW_V:"=!"
            set "NEW_V=!NEW_V: =!"
        )
        set "NEW_V=v!NEW_V!"
        echo [*] Versao real detectada apos download: !NEW_V!
        
        cd /d "%ROOT%\versions"
        rename "main" "!NEW_V!"
        
        set "V_TAG=!NEW_V!"
        set "INIT_V_PATH=%ROOT%\versions\!NEW_V!"
    )
)

:: 5. Configurar Orquestrador na Raiz
echo [*] Configurando Orquestrador e Botoes de Controle...
copy /y "%INIT_V_PATH%\manager\manager.py" "%ROOT%\manager\manager.py"
copy /y "%INIT_V_PATH%\run_eduagenda.bat" "%ROOT%\run_eduagenda.bat"
copy /y "%INIT_V_PATH%\instalação e serviços\2 - Parar Sistema.bat" "%ROOT%\2 - Parar Sistema.bat"

:: 6. Setup do Ambiente Virtual (venv) na versao
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

:: 7. Inicializacao do Banco de Dados
echo [*] Inicializando banco de dados compartilhado...
:: O app.py ja sabe ler EDU_DATA_PATH se o Manager setar, mas aqui rodamos direto
set "EDU_DATA_PATH=%ROOT%\shared\data"
python init_db.py

echo.
echo ==========================================
echo   Instalacao Concluida! 
echo   Versao: %V_TAG%
echo   Local: %ROOT%
echo   
echo   Iniciando o sistema em segundo plano...
echo ==========================================
echo.

:: 8. Auto-Start e Abertura do Navegador
cd /d "%INIT_V_PATH%\instalação e serviços"
if exist "1 - Iniciar Sistema (Oculto).vbs" (
    cscript //nologo "1 - Iniciar Sistema (Oculto).vbs"
    
    :: Tenta capturar o IP local da maquina na rede usando PowerShell
    set "APP_IP=localhost"
    for /f "tokens=*" %%i in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback' -and $_.InterfaceAlias -notmatch 'vEthernet' } | Sort-Object InterfaceMetric | Select-Object -First 1).IPAddress" 2^>nul') do (
        set "APP_IP=%%i"
    )
    
    echo [*] Servidor disparado.
    echo [*] O sistema esta rodando e acessivel na sua rede local em:
    echo     ====================================
    echo     http://!APP_IP!:5000
    echo     ====================================
    echo [*] Compartilhe este link com a sua equipe!
    echo [*] Abrindo painel no navegador padrao em instantes...
    timeout /t 4 /nobreak > nul
    start http://!APP_IP!:5000
) else (
    echo [!] Nao foi possivel iniciar automaticamente. Use o 'run_eduagenda.bat' na raiz: %ROOT%
)

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
