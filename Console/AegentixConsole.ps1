function Start-Kali {
    Write-Host "Launching Kali WSL..." -ForegroundColor Cyan
    wsl -d kali-linux
}

function Start-Ubuntu {
    Write-Host "Launching Ubuntu WSL..." -ForegroundColor Cyan
    wsl -d Ubuntu
}

function Start-AegentixRuntime {
    Write-Host "Checking Aegentix Autonomous Agent Runtime..." -ForegroundColor Cyan
    curl http://localhost:8088/status
}

function Start-GAIA {
    Write-Host "Checking GAIA Agent UI..." -ForegroundColor Cyan
    curl http://localhost:8090
}

function Start-MCP {
    Write-Host "Checking MCP Server..." -ForegroundColor Cyan
    curl http://localhost:8100/status
}

function Aegentix-Panel {
    Clear-Host
    Write-Host "==========================================" -ForegroundColor DarkYellow
    Write-Host "        AEGENTIX CONTROL CONSOLE" -ForegroundColor Yellow
    Write-Host "==========================================" -ForegroundColor DarkYellow
    Write-Host ""
    Write-Host "1. Launch Kali"
    Write-Host "2. Launch Ubuntu"
    Write-Host "3. Check Aegentix Runtime"
    Write-Host "4. Check GAIA Agent UI"
    Write-Host "5. Check MCP Server"
    Write-Host "6. Exit"
    Write-Host ""

    $choice = Read-Host "Select option"

    switch ($choice) {
        "1" { Start-Kali }
        "2" { Start-Ubuntu }
        "3" { Start-AegentixRuntime }
        "4" { Start-GAIA }
        "5" { Start-MCP }
        "6" { return }
        default { Write-Host "Invalid option"; Start-Sleep 1; Aegentix-Panel }
    }
}

Aegentix-Panel
