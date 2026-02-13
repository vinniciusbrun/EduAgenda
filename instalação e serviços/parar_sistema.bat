@echo off
echo Encerrando o servidor de Agenda de Recursos...
taskkill /F /IM pythonw.exe /T
if %errorlevel% neq 0 (
    echo [!] Nao foi possivel encontrar o servidor rodando em segundo plano.
) else (
    echo [OK] Servidor encerrado com sucesso.
)
pause
