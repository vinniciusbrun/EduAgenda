Set WshShell = CreateObject("WScript.Shell")

' Ajusta o diretório de trabalho para a Raiz do Software (subindo 3 níveis: pasta atual -> id da versão -> versions)
WshShell.CurrentDirectory = "..\..\.."

' Executa o orquestrador (manager) invisível via batch intermadiário para carregar o VENV dinâmico
WshShell.Run "cmd.exe /c run_eduagenda.bat", 0, False
