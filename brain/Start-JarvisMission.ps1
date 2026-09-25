param(
    [Parameter(Mandatory=$true)]
    [string]$Objective
)

$Root = "C:\aegentix"

Write-Host "`n=== JARVIS MISSION ===" -ForegroundColor Cyan
Write-Host "Objective: $Objective`n"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is required."
}

Write-Host "[1/3] Recording mission intent..." -ForegroundColor Yellow
python "$Root\brain\cognitive_bus.py" $Objective

Write-Host "`n[2/3] Generating governed plan..." -ForegroundColor Yellow
python "$Root\brain\jarvis\planner.py" $Objective

Write-Host "`n[3/3] Checking model routing..." -ForegroundColor Yellow
python "$Root\brain\router\model_router.py" general

Write-Host "`n=== MISSION INITIALIZED ===" -ForegroundColor Green
Write-Host "AEGENTIX remains authoritative."
Write-Host "Autonomous external execution remains disabled."
