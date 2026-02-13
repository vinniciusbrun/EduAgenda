@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   Agenda de Recursos - Instalador Beta
echo ==========================================

:: 1. Verificar GIT
echo [*] Verificando Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Git nao encontrado. Por favor, instale o Git: https://git-scm.com/
    pause
    exit /b
)

:: 2. Criar VENV se nao existir (no diretorio pai)
cd ..
if not exist "venv" (
    echo [*] Criando ambiente virtual (venv)...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [!] Erro ao criar venv. Verifique se o Python esta no PATH.
        pause
        exit /b
    )
) else (
    echo [*] Ambiente virtual ja existe.
)

:: 3. Instalar Dependencias
echo [*] Atualizando dependencias isoladas...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [!] Erro ao instalar dependencias.
    pause
    exit /b
)

echo.
echo ==========================================
echo   Instalacao Concluida com Sucesso!
echo   Para iniciar: use o arquivo start_hidden.vbs
echo ==========================================
pause
