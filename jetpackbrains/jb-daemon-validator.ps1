Write-Host "[VALIDATOR] Running validator..." -ForegroundColor Yellow

$errors = @()

if (-not (Test-Path "C:\Aegentix\jetpackbrains\jb-daemon.ps1")) { $errors += "Daemon missing" }
if (-not (Test-Path "C:\Aegentix\jetpackbrains\jb-daemon-launcher.cmd")) { $errors += "Launcher missing" }

try { powershell -noprofile -command { . C:\Aegentix\jetpackbrains\jb-daemon.ps1 } } catch { $errors += "Daemon syntax error: $($_.Exception.Message)" }

if ($errors.Count -eq 0) {
    Write-Host "[VALIDATOR] All checks passed" -ForegroundColor Green
} else {
    Write-Host "[VALIDATOR] FAILURES DETECTED:" -ForegroundColor Red
    $errors | ForEach-Object { Write-Host " - $_" -ForegroundColor Red }
}
