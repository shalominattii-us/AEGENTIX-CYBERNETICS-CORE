param()

 = Get-Content -Raw -Path "C:/Aegentix/Kernel/kernel.config.json" | ConvertFrom-Json

function Check-Process {
    param([string], [string])

     = Get-Process -Name  -ErrorAction SilentlyContinue
    if (-not ) {
        Add-Content -Path "/watchdog.log" -Value "[WATCHDOG] Restarting "
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File "
    }
}

while (True) {
    Check-Process -name "powershell" -path .agent_loop
    Check-Process -name "powershell" -path .gaia_sync
    Check-Process -name "powershell" -path .hud_refresh

    Start-Sleep -Seconds 5
}