Set WshShell = CreateObject("WScript.Shell")
' Executa o servidor usando o pythonw do venv (sem janela de terminal)
' O parâmetro 0 oculta a janela
WshShell.Run "..\venv\Scripts\pythonw.exe ..\app.py", 0, False
