@echo off
setlocal

echo ==========================================
echo   EduAgenda - Instalador Automatizado
echo ==========================================

:: 1. Bootstrap de Dependencias (Python e Git)
echo [*] Garantindo Python e Git no sistema...
powershell -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"
if errorlevel 1 goto :bootstrap_fail
goto :bootstrap_ok

:bootstrap_fail
echo [!] Erro no Bootstrap. Verifique a saida acima.
pause
exit /b

:bootstrap_ok
:: Recarregar PATH para reconhecer novas instalacoes
for /f "tokens=*" %%a in ('powershell -command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%a"

:: 2. Definir Alvo e Preparar Pasta
set "TARGET=C:\EduAgenda"
echo [*] Alvo da instalacao: %TARGET%

if not exist "%TARGET%" mkdir "%TARGET%"
cd /d "%TARGET%"

:: 3. Sincronizacao do Repositorio
echo [*] Sincronizando repositorio do EduAgenda...
if not exist ".git" goto :git_clone

echo [i] Repositorio ja existe. Atualizando...
git fetch --all
git reset --hard origin/master
if errorlevel 1 goto :git_main
goto :git_done

:git_clone
git clone https://github.com/vinniciusbrun/EduAgenda.git .
if errorlevel 1 goto :git_error
goto :git_done

:git_main
echo [i] Tentando branch alternativa 'main'...
git reset --hard origin/main
if errorlevel 1 goto :git_error
goto :git_done

:git_error
echo [!] Erro ao sincronizar o repositorio.
pause
exit /b

:git_done
:: 4. Configuracao do Ambiente Virtual (venv)
if exist "venv\Scripts\activate.bat" goto :venv_ok
echo [*] Criando ambiente virtual (venv)...
python -m venv venv
if errorlevel 1 py -m venv venv

:venv_ok
if not exist "venv\Scripts\activate.bat" goto :venv_fail
goto :venv_ready

:venv_fail
echo [!] Falha ao localizar o ambiente virtual.
pause
exit /b

:venv_ready
:: 5. Instalacao de Dependencias
echo [*] Instalando dependencias (isso pode demorar)...
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install --only-binary :all: numpy==1.26.4 pandas==2.2.2 openpyxl==3.1.2
python -m pip install -r requirements.txt
if errorlevel 1 goto :pip_fail
goto :pip_ok

:pip_fail
echo [!] Erro ao instalar dependencias.
pause
exit /b

:pip_ok
:: 6. Inicializacao do Banco de Dados (Root/Admin)
echo [*] Inicializando usuarios administrativos...
python init_db.py

echo.
echo ==========================================
echo   Instalacao Concluida! Iniciando App...
echo ==========================================
echo.

:: 7. Iniciar Servidor
start python app.py

echo [OK] Servidor iniciado. Mantenha essa janela aberta para que o servidor continue funcionando.
timeout /t 5
exit
