function Invoke-JB {
    param([string]$Action)
    switch ($Action) {
        "launch" {
            Write-Host "[JB] Launching full Aegentix ecosystem..." -ForegroundColor Green
            docker compose -f C:\Aegentix\docker-compose.yml up -d
            . C:\Aegentix\sovereign-os\SOVEREIGN_BOOT.ps1
        }
        "status" { docker ps }
        "logs" { docker compose -f C:\Aegentix\docker-compose.yml logs --tail=50 }
        "restart" {
            docker compose -f C:\Aegentix\docker-compose.yml down
            docker compose -f C:\Aegentix\docker-compose.yml up -d
            . C:\Aegentix\sovereign-os\SOVEREIGN_BOOT.ps1
        }
        "heal" {
            docker ps
            . C:\Aegentix\sovereign-os\SOVEREIGN_BOOT.ps1
        }
        "ignite" {
            . C:\Aegentix\jetpackbrains\jb-ignition.ps1
            Start-JetpackBrainsIgnition
        }
        default { Write-Host "[JB] Unknown action: $Action" }
    }
}
