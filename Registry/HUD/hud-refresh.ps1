param()

 = Get-Content -Raw -Path "hud.config.json" | ConvertFrom-Json

while (True) {
    Write-Host "[HUD] Refreshing tactical display..."
    try {
        node "/render.js" | Out-Null
    } catch {
        Add-Content -Path "C:/Aegentix/AgentLoop/Logs/errors.log" -Value "[ERROR] HUD refresh failure: "
    }
    Start-Sleep -Milliseconds .refresh_ms
}