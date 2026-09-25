$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "HERETIC PACKAGE + DEPENDENCY FORENSICS" -ForegroundColor Cyan
Write-Host "READ ONLY — NOTHING WILL BE MODIFIED" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$Py312 = "C:\Program Files\Python312\python.exe"

Write-Host "`n===== PYTHON 3.12 =====" -ForegroundColor Yellow
& $Py312 --version
& $Py312 -c "import sys; print('Executable:',sys.executable); print('Prefix:',sys.prefix); print('Base:',sys.base_prefix)" 2>&1

Write-Host "`n===== HERETIC PACKAGE =====" -ForegroundColor Yellow
& $Py312 -m pip show heretic 2>&1

Write-Host "`n===== HERETIC PACKAGE LOCATION =====" -ForegroundColor Yellow
& $Py312 -c "import heretic,inspect,os; print('Module:',heretic.__file__); print('Directory:',os.path.dirname(heretic.__file__))" 2>&1

Write-Host "`n===== HERETIC VERSION =====" -ForegroundColor Yellow
& $Py312 -c "import importlib.metadata as m; print(m.version('heretic'))" 2>&1

Write-Host "`n===== HERETIC DEPENDENCIES =====" -ForegroundColor Yellow
& $Py312 -m pip show heretic 2>&1 |
    Select-String "Requires|Required-by"

Write-Host "`n===== INSTALLED ML PACKAGES =====" -ForegroundColor Yellow
$Packages = @(
    "torch",
    "transformers",
    "accelerate",
    "safetensors",
    "huggingface-hub",
    "bitsandbytes",
    "datasets",
    "typer",
    "pydantic"
)

foreach ($Package in $Packages) {
    Write-Host "`n[$Package]" -ForegroundColor Cyan
    & $Py312 -m pip show $Package 2>&1 |
        Select-String "Name:|Version:|Location:"
}

Write-Host "`n===== IMPORT TEST =====" -ForegroundColor Yellow

$Imports = @(
    "heretic",
    "torch",
    "transformers",
    "accelerate",
    "safetensors",
    "huggingface_hub",
    "pydantic"
)

foreach ($Module in $Imports) {
    Write-Host "`n[$Module]" -ForegroundColor Cyan
    & $Py312 -c "import importlib; m=importlib.import_module('$Module'); print('OK:',m.__file__); print('Version:',getattr(m,'__version__','n/a'))" 2>&1
}

Write-Host "`n===== HERETIC ENTRY POINT =====" -ForegroundColor Yellow
& $Py312 -c "import importlib.metadata as m; d=m.distribution('heretic'); print('Console scripts:'); [print(x) for x in d.entry_points if x.group=='console_scripts']" 2>&1

Write-Host "`n===== HERETIC FILE TREE =====" -ForegroundColor Yellow
$ModulePath = & $Py312 -c "import heretic,os; print(os.path.dirname(heretic.__file__))" 2>$null

if ($ModulePath -and (Test-Path $ModulePath)) {
    Get-ChildItem -LiteralPath $ModulePath -Recurse -File -ErrorAction SilentlyContinue |
        Select-Object FullName,Length |
        Format-Table -AutoSize
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "PACKAGE FORENSICS COMPLETE — NOTHING MODIFIED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
