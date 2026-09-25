' VBScript to launch GaiaNet Autonomous Suite silently in background on Windows Boot
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File ""C:\Users\eagle\.gemini\antigravity\scratch\gaianet-toolkit\start-autonomy.ps1""", 0, False
