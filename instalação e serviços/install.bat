@echo off
setlocal

echo ==========================================
echo   EduAgenda - Instalador Automatizado
echo ==========================================

:: 1. Bootstrap de Dependências (Python e Git)
echo [*] Garantindo Python e Git no sistema...
powershell -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"
if errorlevel 1 (
    echo [!] Erro no Bootstrap. Verifique a saida acima.
    pause
    exit /b
)

:: Recarregar PATH para reconhecer novas instalações
for /f "tokens=*" %%a in ('powershell -command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%a"

:: 2. Definir Alvo e Preparar Pasta
set "TARGET=C:\EduAgenda"
echo [*] Alvo da instalacao: %TARGET%

if not exist "%TARGET%" (
    echo [*] Criando pasta de destino...
    mkdir "%TARGET%"
)

cd /d "%TARGET%"

:: 3. Clone do Repositório
echo [*] Clonando repositorio do EduAgenda...
if exist ".git" (
    echo [i] Repositorio ja existe. Atualizando...
    git pull origin master || git pull origin main
) else (
    git clone https://github.com/vinniciusbrun/EduAgenda.git .
)

if errorlevel 1 (
    echo [!] Erro ao clonar/atualizar o repositorio.
    pause
    exit /b
)

:: 4. Configuração do Ambiente Virtual (venv)
if not exist "venv" (
    echo [*] Criando ambiente virtual (venv)...
    python -m venv venv || py -m venv venv
)

if not exist "venv\Scripts\activate.bat" (
    echo [!] Falha ao localizar o ambiente virtual.
    pause
    exit /b
)

:: 5. Instalação de Dependências
echo [*] Instalando dependencias (isso pode demorar)...
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install --only-binary :all: numpy==1.26.4 pandas==2.2.2 openpyxl==3.1.2
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo [!] Erro ao instalar dependencias.
    pause
    exit /b
)

echo.
echo ==========================================
echo   Instalacao Concluida! Iniciando App...
echo ==========================================
echo.

:: 6. Iniciar Servidor
:: Tenta rodar o app diretamente
start python app.py

echo [OK] Servidor iniciado. Voce pode fechar esta janela.
timeout /t 5
exit
