@echo off
setlocal

echo ==========================================
echo   EduAgenda - Instalador e Configurador
echo ==========================================

:: 1. Bootstrap de Dependencias (Python e Git)
echo [*] Iniciando auto-instalador de dependencias...
powershell -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"

:: Recarregar PATH para esta sessao (Simulacao via PS)
for /f "tokens=*" %%a in ('powershell -command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%a"

:: 2. Verificar Python Pos-Bootstrap
echo [*] Validando ambiente...
python --version >nul 2>&1
if errorlevel 1 goto :python_still_missing

:: Detectar versao para logs
for /f "tokens=2 delims= " %%v in ('python --version') do (
    set PY_VER=%%v
)
echo [*] Python OK: %PY_VER%

:: 3. Verificar GIT Pos-Bootstrap
git --version >nul 2>&1
if errorlevel 1 goto :git_still_missing

:: 4. Detectar se o projeto ja existe aqui ou em cima
if exist "app.py" (
    set BASE_DIR=.
    goto :files_found
)
if exist "..\app.py" (
    set BASE_DIR=..
    goto :files_found
)

:: 5. Se nao encontrou, e uma instalacao "Zero" (Sincronizar)
echo [!] Arquivos do sistema nao encontrados nesta pasta.
set /p clone="Deseja baixar (Sincronizar) o EduAgenda do GitHub agora? (S/N): "
if /i "%clone%" neq "s" goto :no_files

echo [*] Inicializando e baixando arquivos (Sincronizando)...
git init >nul 2>&1
git remote add origin https://github.com/vinniciusbrun/EduAgenda.git >nul 2>&1
git pull origin master
if errorlevel 1 goto :clone_error

set BASE_DIR=.
goto :files_found

:no_files
echo [!] Erro: Nao foi possivel localizar ou baixar os arquivos do projeto.
pause
exit /b

:files_found
cd /d "%BASE_DIR%"

:: 6. Criar VENV
if exist "venv" goto :venv_exists
echo [*] Criando ambiente virtual (venv)...
python -m venv venv
if errorlevel 1 goto :venv_error
goto :venv_done

:venv_exists
echo [*] Ambiente virtual ja existe.
:venv_done

:: 7. Instalar Dependencias
echo [*] Configurando ambiente Python...
if not exist "venv\Scripts\activate.bat" goto :venv_missing
call "venv\Scripts\activate.bat"

echo [*] Atualizando instalador (pip)...
python -m pip install --upgrade pip

echo [*] Instalando bibliotecas base (Modo Binario Forcado)...
python -m pip install --only-binary :all: numpy==1.26.4 pandas==2.2.2 openpyxl==3.1.2
if errorlevel 1 goto :binary_error

echo [*] Instalando demais requisitos...
python -m pip install --prefer-binary -r requirements.txt
if errorlevel 1 goto :pip_error

echo.
echo ==========================================
echo   Instalacao Concluida com Sucesso! 🚀
echo ==========================================
echo   PROXIMOS PASSOS:
echo   1. Use o arquivo 'start_hidden.vbs' para iniciar.
echo   2. No sistema, va em 'Configuracoes' para 
echo      vincular seu GitHub e ativar atualizacoes.
echo ==========================================
pause
exit /b

:python_still_missing
echo [!] ERRO CRITICO: Python nao pode ser instalado ou configurado.
echo [!] Tente instalar manualmente em: https://www.python.org/downloads/
pause
exit /b

:git_still_missing
echo [!] ERRO CRITICO: Git nao pode ser instalado ou configurado.
echo [!] Tente instalar manualmente em: https://git-scm.com/
pause
exit /b

:clone_error
echo [!] Erro ao sincronizar. Verifique sua internet ou se o repositorio e acessivel.
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
echo [!] ERRO: Nao foi possivel encontrar bibliotecas prontas para o Python %PY_VER%.
echo [!] O Bootstrap tentou instalar o 3.12, mas algo impediu o uso.
echo [!] RECOMENDACAO: Desinstale outras versoes do Python e tente novamente.
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
