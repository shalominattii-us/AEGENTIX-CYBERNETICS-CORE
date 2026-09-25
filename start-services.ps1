Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File C:/Aegentix/AgentLoop/agent-loop.ps1'
Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File C:/Aegentix/Registry/Gaia/gaia-sync.ps1'
Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File C:/Aegentix/Registry/HUD/hud-refresh.ps1'