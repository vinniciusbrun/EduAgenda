@echo off
setlocal

echo ==========================================
echo   EduAgenda - Instalador e Configurador
echo ==========================================

:: Detectar se estamos na pasta raiz ou em 'instalacao e servicos'
if exist "app.py" (
    set BASE_DIR=.
) else if exist "..\app.py" (
    set BASE_DIR=..
) else (
    echo [!] Erro: Nao foi possivel localizar os arquivos do projeto.
    echo [!] Execute este script a partir da pasta do EduAgenda.
    pause
    exit /b
)

:: 1. Verificar Python
echo [*] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 goto :no_python

:: 2. Verificar GIT
echo [*] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 goto :no_git

:: 3. Mover para a base do projeto
cd /d "%BASE_DIR%"

:: 4. Criar VENV se nao existir
if exist "venv" goto :venv_exists
echo [*] Criando ambiente virtual (venv)...
python -m venv venv
if errorlevel 1 goto :venv_error
goto :venv_done

:venv_exists
echo [*] Ambiente virtual ja existe.
:venv_done

:: 5. Garantir Git Init
if exist ".git" goto :git_ready
echo [*] Inicializando repositorio Git para atualizacoes...
git init >nul 2>&1
git config user.name "Usuario EduAgenda"
git config user.email "usuario@eduagenda.local"
:git_ready

:: 6. Instalar Dependencias
echo [*] Instalando/Atualizando dependencias...
if not exist "venv\Scripts\activate.bat" goto :venv_missing
call "venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
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

:no_python
echo [!] Python nao encontrado no PATH.
echo [!] Por favor, instale o Python e MARQUE a opcao 'Add Python to PATH'.
pause
exit /b

:no_git
echo [!] Git nao encontrado.
echo [!] 1. Baixe e instale: https://git-scm.com/
echo [!] 2. Apos instalar, REINICIE este terminal ou o computador.
echo [!] 3. Execute este instalador novamente.
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
