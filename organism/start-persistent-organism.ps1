$ErrorActionPreference = "Stop"
$OrgRoot = "C:\\aegentix\\organism"
$Python  = "C:\\Program Files\\Python312\\python.exe"
$Script  = Join-Path $OrgRoot "self-awareness\\self-awareness.py"
Write-Host "Starting Aegentix organism..." -ForegroundColor Cyan
& $Python $Script
