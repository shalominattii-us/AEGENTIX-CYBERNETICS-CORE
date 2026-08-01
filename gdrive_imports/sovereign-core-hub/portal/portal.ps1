# ================================
# SOVEREIGN PORTAL — INTERACTIVE UI (V2 CLEAN)
# ================================

$ErrorActionPreference = 'Stop'

function Show-Dashboard {
    Clear-Host
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║        S O V E R E I G N   P O R T A L   ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""

    $id = Get-Content C:\SOVEREIGN\identity.json | ConvertFrom-Json

    Write-Host " Node: $($id.nodeName)" -ForegroundColor Yellow
    Write-Host " User: $($id.user)"
    Write-Host " ID:   $($id.id)"
    Write-Host " Created: $($id.createdAt)"
    Write-Host ""

    Write-Host " System Status:" -ForegroundColor Cyan
    Write-Host "  • Kernel............. ONLINE"
    Write-Host "  • Worlds Engine...... READY"
    Write-Host "  • Portal............. ACTIVE"
    Write-Host ""

    Write-Host " Recent Logs:" -ForegroundColor Cyan
    $logs = Get-ChildItem C:\SOVEREIGN\logs -File | Sort-Object LastWriteTime -Descending
    if ($logs.Count -eq 0) {
        Write-Host "  (no logs yet)"
    } else {
        $logs | Select-Object -First 3 | ForEach-Object {
            Write-Host "  - $($_.Name)"
        }
    }

    Write-Host ""
    Write-Host " Commands:" -ForegroundColor Cyan
    Write-Host "  dashboard   - refresh dashboard"
    Write-Host "  menu        - show menu"
    Write-Host "  exit        - exit portal"
    Write-Host ""
}

function Show-Menu {
    Write-Host ""
    Write-Host "Select an option:" -ForegroundColor Yellow
    Write-Host " 1) Kernel Status"
    Write-Host " 2) Worlds Engine"
    Write-Host " 3) Identity"
    Write-Host " 4) Logs"
    Write-Host " 5) Exit Portal"
    Write-Host ""
}

function Show-KernelStatus {
    Write-Host ""
    Write-Host "[ Kernel Status ]" -ForegroundColor Cyan
    Write-Host "Kernel file: C:\SOVEREIGN\kernel\kernel.ps1"
    Write-Host "Mode: default"
    Write-Host ""
}

function Show-Worlds {
    Write-Host ""
    Write-Host "[ Worlds Engine ]" -ForegroundColor Cyan
    Write-Host "Worlds file: C:\SOVEREIGN\worlds\worlds.ps1"
    Write-Host "Status: Ready"
    Write-Host ""
}

function Show-Identity {
    Write-Host ""
    Write-Host "[ Identity ]" -ForegroundColor Cyan
    $id = Get-Content C:\SOVEREIGN\identity.json | ConvertFrom-Json
    Write-Host "Node ID: $($id.id)"
    Write-Host "Node Name: $($id.nodeName)"
    Write-Host "User: $($id.user)"
    Write-Host "Created: $($id.createdAt)"
    Write-Host ""
}

function Show-Logs {
    Write-Host ""
    Write-Host "[ Logs ]" -ForegroundColor Cyan
    $logs = Get-ChildItem C:\SOVEREIGN\logs -File | Sort-Object LastWriteTime -Descending
    if ($logs.Count -eq 0) {
        Write-Host "No logs found."
    } else {
        Write-Host "Recent logs:"
        $logs | Select-Object -First 5 | ForEach-Object {
            Write-Host " - $($_.Name)"
        }
    }
    Write-Host ""
}

# ================================
# MAIN LOOP
# ================================

Show-Dashboard

while ($true) {
    $choice = Read-Host "portal"

    switch ($choice.ToLower()) {
        "1" { Show-KernelStatus }
        "2" { Show-Worlds }
        "3" { Show-Identity }
        "4" { Show-Logs }
        "5" { break }
        "dashboard" { Show-Dashboard }
        "menu" { Show-Menu }
        "exit" { break }
        default { Write-Host "Unknown command." -ForegroundColor Red }
    }
}

Write-Host ""
Write-Host "Exiting Sovereign Portal..." -ForegroundColor Yellow
Write-Host ""
