param()

 = Get-Content -Raw -Path "gaia.config.json" | ConvertFrom-Json

while (True) {
    Write-Host "[GAIA] Syncing node..."
    try {
        node "/index.js" | Out-Null
        node "/index.js" | Out-Null
    } catch {
        Add-Content -Path "C:/Aegentix/AgentLoop/Logs/errors.log" -Value "[ERROR] GAIA sync failure: "
    }
    Start-Sleep -Milliseconds .sync_interval_ms
}