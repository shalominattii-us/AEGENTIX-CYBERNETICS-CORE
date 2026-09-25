param()

 = Get-Content -Raw -Path "C:/Aegentix/Kernel/kernel.config.json" | ConvertFrom-Json

Add-Content -Path "/recovery.log" -Value "[RECOVERY] Triggered"

Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File .agent_loop"
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File .gaia_sync"
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File .hud_refresh"