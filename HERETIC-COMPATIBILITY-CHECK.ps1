$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "HERETIC MODEL COMPATIBILITY CHECK" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n===== HERETIC PACKAGE =====" -ForegroundColor Yellow
$HereticExe = (Get-Command heretic).Source
Write-Host "Executable: $HereticExe"

$Py312 = "C:\Users\eagle\AppData\Roaming\Python\Python312\python.exe"

if (Test-Path $Py312) {
    & $Py312 -c "import heretic,sys; print('Python:',sys.executable); print('Heretic:',getattr(heretic,'__file__','unknown')); print('Version:',getattr(heretic,'__version__','unknown'))" 2>&1
}
else {
    Write-Host "Python 3.12 executable not found at expected path." -ForegroundColor Yellow
}

Write-Host "`n===== PYTORCH / TRANSFORMERS / ACCELERATE =====" -ForegroundColor Yellow

if (Test-Path $Py312) {
    & $Py312 -c "mods=['torch','transformers','accelerate','safetensors']; [print(m+': '+str(getattr(__import__(m),'__version__','unknown'))) for m in mods]" 2>&1
}

Write-Host "`n===== OLLAMA MODEL METADATA =====" -ForegroundColor Yellow

try {
    $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 5

    foreach ($m in $tags.models) {
        Write-Host "`nMODEL: $($m.name)" -ForegroundColor Cyan

        try {
            $show = Invoke-RestMethod `
                -Uri "http://127.0.0.1:11434/api/show" `
                -Method Post `
                -ContentType "application/json" `
                -Body (@{name=$m.name} | ConvertTo-Json) `
                -TimeoutSec 10

            [PSCustomObject]@{
                Name       = $m.name
                Size       = $m.size
                Format     = $show.details.format
                Family     = $show.details.family
                ParameterSize = $show.details.parameter_size
                Quantization = $show.details.quantization_level
            } | Format-List
        }
        catch {
            Write-Host "Metadata query failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
catch {
    Write-Host "Ollama API ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n===== HERETIC CONFIG FILES — PATHS ONLY =====" -ForegroundColor Yellow

@(
    "$env:USERPROFILE\.config\heretic\config.toml",
    "$env:APPDATA\heretic\config.toml",
    "$env:LOCALAPPDATA\heretic\config.toml",
    "$env:USERPROFILE\.heretic\config.toml"
) | ForEach-Object {
    if (Test-Path $_) {
        Write-Host $_
    }
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "READ-ONLY COMPATIBILITY CHECK COMPLETE" -ForegroundColor Green
Write-Host "NO CONFIGURATION CHANGED" -ForegroundColor Green
Write-Host "NO MODEL CHANGED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
