# ================================
# SOVEREIGN PORTAL — INTERACTIVE UI (V2 CLEAN)
# ================================

$ErrorActionPreference = 'Stop'

Write-Host ""
Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        S O V E R E I G N   P O R T A L   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

function Show-Menu {
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
    Write-Host "Kernel file: C:\Sovereign\kernel\kernel.ps1"
    Write-Host "Mode: default"
    Write-Host ""
}

function Show-Worlds {
    Write-Host ""
    Write-Host "[ Worlds Engine ]" -ForegroundColor Cyan
    Write-Host "Worlds file: C:\Sovereign\worlds\worlds.ps1"
    Write-Host "Status: Ready"
    Write-Host ""
}

function Show-Identity {
    Write-Host ""
    Write-Host "[ Identity ]" -ForegroundColor Cyan
    $id = Get-Content C:\Sovereign\identity.json | ConvertFrom-Json
    Write-Host "Node ID: $($id.id)"
    Write-Host "Node Name: $($id.nodeName)"
    Write-Host "User: $($id.user)"
    Write-Host "Created: $($id.createdAt)"
    Write-Host ""
}

function Show-Logs {
    Write-Host ""
    Write-Host "[ Logs ]" -ForegroundColor Cyan
    $logs = Get-ChildItem C:\Sovereign\logs -File | Sort-Object LastWriteTime -Descending
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

while ($true) {
    Show-Menu
    $choice = Read-Host "Enter choice"

    switch ($choice) {
        "1" { Show-KernelStatus }
        "2" { Show-Worlds }
        "3" { Show-Identity }
        "4" { Show-Logs }
        "5" { break }
        default { Write-Host "Invalid option." -ForegroundColor Red }
    }
}

Write-Host ""
Write-Host "Exiting Sovereign Portal..." -ForegroundColor Yellow
Write-Host ""
