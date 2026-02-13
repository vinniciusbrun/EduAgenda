@echo off
setlocal

echo ==========================================
echo   EduAgenda - Instalador e Configurador
echo ==========================================

:: 1. Verificar Python
echo [*] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 goto :no_python

:: Detectar versao experimental (3.14+)
for /f "tokens=2 delims= " %%v in ('python --version') do (
    set PY_VER=%%v
)
echo [*] Versao detectada: %PY_VER%
if "%PY_VER:~0,4%"=="3.14" goto :experimental_python
if "%PY_VER:~0,4%"=="3.15" goto :experimental_python

:: 2. Verificar GIT
echo [*] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 goto :no_git

:: 3. Detectar se o projeto ja existe aqui ou em cima
if exist "app.py" (
    set BASE_DIR=.
    goto :files_found
)
if exist "..\app.py" (
    set BASE_DIR=..
    goto :files_found
)

:: 4. Se nao encontrou, e uma instalacao "Zero"
echo [!] Arquivos do sistema nao encontrados nesta pasta.
set /p clone="Deseja baixar (Sincronizar) o EduAgenda do GitHub agora? (S/N): "
if /i "%clone%" neq "s" goto :no_files

echo [*] Inicializando e baixando arquivos (Sincronizando)...
:: Garante que pastas com arquivos ocultos nao travem o processo
git init >nul 2>&1
git remote add origin https://github.com/vinniciusbrun/EduAgenda.git >nul 2>&1
git pull origin master
if errorlevel 1 goto :clone_error

set BASE_DIR=.
goto :files_found

:no_files
echo [!] Erro: Nao foi possivel localizar os arquivos do projeto.
echo [!] Certifique-se de estar na pasta correta ou responda 'S' para baixar.
pause
exit /b

:files_found
cd /d "%BASE_DIR%"

:: 5. Criar VENV
if exist "venv" goto :venv_exists
echo [*] Criando ambiente virtual (venv)...
python -m venv venv
if errorlevel 1 goto :venv_error
goto :venv_done

:venv_exists
echo [*] Ambiente virtual ja existe.
:venv_done

:: 6. Instalar Dependencias
echo [*] Configurando ambiente Python...
if not exist "venv\Scripts\activate.bat" goto :venv_missing
call "venv\Scripts\activate.bat"

echo [*] Atualizando instalador (pip)...
python -m pip install --upgrade pip

echo [*] Instalando bibliotecas base (Modo Binario Forcado)...
:: Forca o uso de binarios (wheels) para evitar erros de compilacao. 
:: Python 3.11/3.12 tem wheels prontos. 3.14+ Nao tem.
python -m pip install --only-binary :all: numpy==1.26.4 pandas==2.2.2 openpyxl==3.1.2
if errorlevel 1 goto :binary_error

echo [*] Instalando demais requisitos...
python -m pip install --prefer-binary -r requirements.txt
if errorlevel 1 goto :pip_error

echo.
echo ==========================================
echo   Instalacao Concluida com Sucesso!
echo ==========================================
echo   PROXIMOS PASSOS:
echo   1. Use o arquivo 'start_hidden.vbs' para iniciar.
echo   2. No sistema, va em 'Configuracoes' para 
echo      vincular seu GitHub e ativar atualizacoes.
echo ==========================================
pause
exit /b

:experimental_python
echo.
echo [!] ALERTA: Voce esta usando o Python %PY_VER% (Experimental).
echo [!] Bibliotecas como 'numpy' e 'pandas' ainda NAO tem arquivos prontos
echo [!] para esta versao do Python. A instalacao vai falhar.
echo [!] RECOMENDACAO: Instale o Python 3.11 ou 3.12 (Estaveis).
echo.
pause
exit /b

:no_python
echo [!] Python nao encontrado no PATH.
echo [!] Por favor, instale o Python e MARQUE a opcao 'Add Python to PATH'.
pause
exit /b

:no_git
echo [!] Git nao encontrado. Instale: https://git-scm.com/
pause
exit /b

:clone_error
echo [!] Erro ao sincronizar. Verifique se a pasta esta vazia ou se ha internet.
pause
exit /b

:venv_error
echo [!] Erro ao criar venv. 
pause
exit /b

:venv_missing
echo [!] Erro: Ambiente virtual nao encontrado (venv).
pause
exit /b

:pip_error
echo [!] Erro ao instalar dependencias.
pause
exit /b

:binary_error
echo.
echo [!] ERRO: Nao foi possivel encontrar bibliotecas prontas para seu Python.
echo [!] Isso acontece porque sua versao do Python e muito nova ou 32-bits.
echo [!] RECOMENDACAO: Use Python 3.11 ou 3.12 (64-bits).
echo.
pause
exit /b

:no_python
echo [!] Python nao encontrado no PATH.
echo [!] Por favor, instale o Python e MARQUE a opcao 'Add Python to PATH'.
pause
exit /b

:no_git
echo [!] Git nao encontrado. Instale: https://git-scm.com/
pause
exit /b

:clone_error
echo [!] Erro ao clonar o repositorio. Verifique sua conexao.
pause
exit /b

:venv_error
echo [!] Erro ao criar venv. 
pause
exit /b

:venv_missing
echo [!] Erro: Ambiente virtual nao encontrado (venv).
pause
exit /b

:pip_error
echo [!] Erro ao instalar dependencias. Verifique sua conexao.
pause
exit /b
