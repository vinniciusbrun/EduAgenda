@echo off
setlocal

echo ==========================================
echo   EduAgenda - Instalador e Configurador
echo ==========================================

:: 1. Bootstrap de Dependencias (Python e Git)
echo [*] Iniciando auto-instalador de dependencias...
powershell -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"
if errorlevel 1 (
    echo [!] Erro no Bootstrap. Verifique saida anterior.
    pause
    exit /b
)

:: Recarregar PATH de forma agressiva
for /f "tokens=*" %%a in ('powershell -command "[System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')"') do set "PATH=%%a"

:: 2. Verificar Python Pos-Bootstrap
echo [*] Validando ambiente...

set PY_CMD=
py -0 >nul 2>&1
if not errorlevel 1 (
    set PY_CMD=py
    goto :python_ok
)

for /f "tokens=*" %%p in ('where python 2^>nul') do (
    echo %%p | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        set PY_CMD=python
        goto :python_ok
    )
)

if exist "%ProgramFiles%\Python312\python.exe" (
    set "PY_CMD=%ProgramFiles%\Python312\python.exe"
    goto :python_ok
)
if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    set "PY_CMD=%LocalAppData%\Programs\Python\Python312\python.exe"
    goto :python_ok
)

goto :python_still_missing

:python_ok
for /f "tokens=*" %%v in ('%PY_CMD% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2^>nul') do (
    set PY_VER=%%v
)
if "%PY_VER%"=="" goto :python_still_missing

echo [*] Python detectado: %PY_VER% (%PY_CMD%)

:: 3. Verificar GIT Pos-Bootstrap
git --version >nul 2>&1
if errorlevel 1 goto :git_still_missing

:: 4. Detectar o Diretorio Raiz do Projeto
set "SCRIPT_DIR=%~dp0"
echo.
echo [i] Diagnosticando caminhos...
echo     Script: %SCRIPT_DIR%

:: Logica simplificada sem DelayedExpansion
if exist "%SCRIPT_DIR%..\app.py" (
    echo [*] App detectado no diretorio pai.
    pushd "%SCRIPT_DIR%.."
    goto :found_root
)

if exist "%SCRIPT_DIR%app.py" (
    echo [*] App detectado no mesmo diretorio.
    pushd "%SCRIPT_DIR%"
    goto :found_root
)

echo.
echo [!] ERRO CRITICO: app.py nao encontrado.
echo     Procurado em:
echo     1. %SCRIPT_DIR%..\app.py
echo     2. %SCRIPT_DIR%app.py
echo.
pause
exit /b

:found_root
set "TARGET_DIR=%CD%"
echo [*] Raiz definida como: %TARGET_DIR%
popd
cd /d "%TARGET_DIR%"
if "%CD%"=="C:\" (
    echo [!] ERRO: Nao e permitido instalar o sistema na raiz do disco (C:\).
    echo [!] Crie uma pasta (ex: C:\EduAgenda) e coloque o instalador la.
    pause
    exit /b
)

echo [*] Pasta de instalacao: %CD%

:: 4.1 Verificar se o projeto ja existe
if exist "app.py" (
    set BASE_DIR=.
    goto :files_found
)

:: 5. Instalacao "Zero" (Sincronizar Repositorio)
echo.
echo [!] Sistema nao detectado em: %TARGET_DIR%
set /p clone="Deseja baixar (Sincronizar) o EduAgenda completo agora? (S/N): "
if /i "%clone%" neq "s" goto :no_files

echo [*] Inicializando repositorio Git...
git init
if errorlevel 1 goto :git_error

git remote add origin https://github.com/vinniciusbrun/EduAgenda.git >nul 2>&1

echo [*] Baixando arquivos do sistema (Sincronismo Forçado)...
echo [*] Isso pode demorar alguns minutos dependendo da sua internet.
git fetch --all --depth 1
if errorlevel 1 (
    echo [!] Erro ao conectar com o GitHub. Verifique sua internet.
    pause
    exit /b
)

:: Tenta master primeiro, depois main
echo [*] Restaurando arquivos (master)...
git reset --hard origin/master >nul 2>&1
if errorlevel 1 (
    echo [*] Tentando branch alternativa (main)...
    git reset --hard origin/main >nul 2>&1
)

if errorlevel 1 goto :clone_error

:: Verifica se baixou o essencial
if not exist "requirements.txt" (
    echo [!] ERRO: Sincronismo concluido, mas 'requirements.txt' ainda falta.
    echo [!] Verifique se voce tem permissoes de escrita nesta pasta.
    pause
    exit /b
)

set BASE_DIR=.
goto :files_found

:no_files
echo [!] Cancelado. Nao foi possivel localizar os arquivos do projeto.
pause
exit /b

:git_error
echo [!] Erro ao inicializar o Git no diretorio atual. Verifique permissoes.
pause
exit /b

:files_found
cd /d "%BASE_DIR%"

:: 6. Criar VENV
if exist "venv" goto :venv_exists
echo [*] Criando ambiente virtual (venv)...
%PY_CMD% -m venv venv
if errorlevel 1 (
    echo [!] Erro ao criar ambiente virtual com '%PY_CMD%'. Tentando com 'python'...
    python -m venv venv
)
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
