$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "HERETIC RUNTIME OWNERSHIP + DEPENDENCY FORENSICS" -ForegroundColor Cyan
Write-Host "READ ONLY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n===== HERETIC EXECUTABLE =====" -ForegroundColor Yellow
$cmd = Get-Command heretic -ErrorAction SilentlyContinue
$cmd | Format-List Name,Source,Definition

$exe = $cmd.Source

if ($exe) {
    Write-Host "`n===== HERETIC LAUNCHER CONTENT =====" -ForegroundColor Yellow
    Get-Content -LiteralPath $exe -ErrorAction SilentlyContinue |
        Select-Object -First 80
}

Write-Host "`n===== PYTHON INSTALLATIONS =====" -ForegroundColor Yellow
Get-Command python,python3,py -All -ErrorAction SilentlyContinue |
    Select-Object Name,Source,Definition |
    Format-Table -AutoSize

Write-Host "`n===== PYTHON VERSION(S) =====" -ForegroundColor Yellow

$PythonCommands = @(
    "python",
    "python3",
    "py"
)

foreach ($pc in $PythonCommands) {
    $found = Get-Command $pc -ErrorAction SilentlyContinue
    if ($found) {
        Write-Host "`n[$pc]" -ForegroundColor Cyan
        & $pc --version 2>&1
        & $pc -c "import sys; print(sys.executable)" 2>&1
    }
}

Write-Host "`n===== PYTHON USER SCRIPT DIRECTORIES =====" -ForegroundColor Yellow

$ScriptDirs = @(
    "$env:APPDATA\Python",
    "$env:LOCALAPPDATA\Programs\Python",
    "C:\Python312",
    "C:\Python313",
    "C:\Python314",
    "C:\Users\eagle\AppData\Local\Programs\Python"
)

foreach ($d in $ScriptDirs) {
    if (Test-Path $d) {
        Write-Host "`nDIRECTORY: $d" -ForegroundColor Green
        Get-ChildItem -LiteralPath $d -Recurse -File -Filter "python.exe" -ErrorAction SilentlyContinue |
            Select-Object -ExpandProperty FullName
    }
}

Write-Host "`n===== HERETIC PACKAGE FILES =====" -ForegroundColor Yellow

$HereticDirs = @(
    "$env:APPDATA\Python\Python312\site-packages",
    "$env:APPDATA\Python\Python313\site-packages",
    "$env:APPDATA\Python\Python314\site-packages",
    "$env:LOCALAPPDATA\Programs\Python"
)

foreach ($d in $HereticDirs) {
    if (Test-Path $d) {
        Get-ChildItem -LiteralPath $d -Recurse -File -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -match '(?i)heretic|transformers|torch|accelerate|safetensors'
            } |
            Select-Object -First 100 FullName,Length |
            Format-Table -AutoSize
    }
}

Write-Host "`n===== PIP HERETIC RECORD =====" -ForegroundColor Yellow

$Pips = @(
    "pip",
    "pip3",
    "py -m pip"
)

foreach ($pip in $Pips) {
    Write-Host "`n[$pip]" -ForegroundColor Cyan
    try {
        if ($pip -eq "py -m pip") {
            & py -m pip show heretic 2>&1
        }
        else {
            & $pip show heretic 2>&1
        }
    }
    catch {}
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "FORENSICS COMPLETE — NOTHING MODIFIED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
