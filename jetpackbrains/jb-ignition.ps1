# JetpackBrains Sovereign Ignition
function Start-JetpackBrainsIgnition {
    Write-Host "[JB-IGNITION] Sovereign OS ignition fired." -ForegroundColor Red
    . 'C:\Aegentix\jetpackbrains\jb-global.ps1'
    Invoke-JBGlobal -Caller 'SOVEREIGN-OS-IGNITION'
}
