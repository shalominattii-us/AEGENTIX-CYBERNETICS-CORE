$ErrorActionPreference = "Continue"

$Py = "C:\Program Files\Python312\python.exe"
$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$Backup = "C:\Aegentix\HERETIC-BACKUP-$Stamp"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AEGENTIX — REPAIR HERETIC INSTALLATION" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $Backup | Out-Null

Write-Host "`n[1/6] Backing up existing Heretic configuration..." -ForegroundColor Yellow

$Configs = @(
    "$env:USERPROFILE\.config\heretic\config.toml",
    "$env:APPDATA\heretic\config.toml",
    "$env:LOCALAPPDATA\heretic\config.toml",
    "$env:USERPROFILE\.heretic\config.toml"
)

foreach ($Config in $Configs) {
    if (Test-Path -LiteralPath $Config) {
        $Safe = ($Config -replace '[:\\\/]','_')
        Copy-Item -LiteralPath $Config -Destination (Join-Path $Backup $Safe) -Force
        Write-Host "BACKED UP: $Config" -ForegroundColor Green
    }
}

Write-Host "`n[2/6] Confirming Python..." -ForegroundColor Yellow
& $Py --version

Write-Host "`n[3/6] Repairing Heretic package metadata..." -ForegroundColor Yellow
& $Py -m pip install --user --force-reinstall --no-deps heretic-llm

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Heretic package repair failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n[4/6] Verifying pip registration..." -ForegroundColor Yellow
& $Py -m pip show heretic-llm
& $Py -m pip show heretic

Write-Host "`n[5/6] Verifying Python import..." -ForegroundColor Yellow
& $Py -c "import heretic,sys; print('HERETIC IMPORT:',heretic.__file__); print('PYTHON:',sys.executable)" 2>&1

Write-Host "`n[6/6] Verifying Heretic CLI..." -ForegroundColor Yellow
$HereticExe = "$env:APPDATA\Python\Python312\Scripts\heretic.exe"

if (Test-Path -LiteralPath $HereticExe) {
    Write-Host "EXECUTABLE: $HereticExe" -ForegroundColor Green
    & $HereticExe --help 2>&1 | Select-Object -First 25
}
else {
    Write-Host "WARNING: Expected executable not found at $HereticExe" -ForegroundColor Yellow
    Get-Command heretic -ErrorAction SilentlyContinue |
        Select-Object Name,Source,Definition |
        Format-List
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "HERETIC REPAIR COMPLETE" -ForegroundColor Green
Write-Host "Config backup: $Backup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
