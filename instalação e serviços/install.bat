@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo   EduAgenda - Instalador e Configurador
echo ==========================================

:: 1. Verificar Python
echo [*] Verificando Python...
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [!] Python nao encontrado no PATH.
    echo [!] Por favor, instale o Python e MARQUE a opcao 'Add Python to PATH'.
    pause
    exit /b
)

:: 2. Verificar GIT
echo [*] Verificando Git...
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Git nao encontrado.
    echo [!] 1. Baixe e instale: https://git-scm.com/
    echo [!] 2. Apos instalar, REINICIE este terminal ou o computador.
    echo [!] 3. Execute este instalador novamente.
    pause
    exit /b
)

:: 3. Criar VENV se nao existir (no diretorio pai)
cd ..
if not exist "venv" (
    echo [*] Criando ambiente virtual (venv)...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [!] Erro ao criar venv.
        pause
        exit /b
    )
) else (
    echo [*] Ambiente virtual ja existe.
)

:: 4. Garantir que e um repositorio Git (para atualizacoes)
if not exist ".git" (
    echo [*] Inicializando repositorio Git para atualizacoes...
    git init >nul 2>&1
    git config user.name "Usuario EduAgenda"
    git config user.email "usuario@eduagenda.local"
)

:: 5. Instalar Dependencias
echo [*] Instalando/Atualizando dependencias...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [!] Erro ao instalar dependencias. Verifique sua conexao.
    pause
    exit /b
)

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
