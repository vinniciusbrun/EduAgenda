@echo off
setlocal

set "VBS_NAME=start_hidden.vbs"
set "VBS_PATH=%~dp0%VBS_NAME%"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\AgendaRecursos.lnk"

echo ==========================================
echo   Ativador de Inicio Automatico
echo ==========================================

echo [*] Localizando script: %VBS_PATH%

:: Criar atalho via PowerShell
powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%SHORTCUT_PATH%');$s.TargetPath='%VBS_PATH%';$s.WorkingDirectory='%~dp0..';$s.Save()"

if %errorlevel% equ 0 (
    echo [OK] O sistema agora iniciara automaticamente com o Windows!
    echo [i] Ativado em: %SHORTCUT_PATH%
) else (
    echo [!] Falha ao criar atalho de inicializacao.
)

pause
