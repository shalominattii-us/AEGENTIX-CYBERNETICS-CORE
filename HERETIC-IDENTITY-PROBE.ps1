$ErrorActionPreference = "Continue"

$Py = "C:\Program Files\Python312\python.exe"
$Site = "C:\Users\eagle\AppData\Roaming\Python\Python312\site-packages"
$Heretic = Join-Path $Site "heretic"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "HERETIC IDENTITY + INSTALLATION PROBE" -ForegroundColor Cyan
Write-Host "READ ONLY — NOTHING WILL BE MODIFIED" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n===== EXECUTABLE METADATA =====" -ForegroundColor Yellow
Get-Item "C:\Users\eagle\AppData\Roaming\Python\Python312\Scripts\heretic.exe" |
    Select-Object FullName,Length,CreationTime,LastWriteTime |
    Format-List

Write-Host "`n===== HERETIC PACKAGE DIRECTORY =====" -ForegroundColor Yellow
Get-ChildItem -LiteralPath $Heretic -File |
    Select-Object Name,Length,LastWriteTime |
    Sort-Object Name |
    Format-Table -AutoSize

Write-Host "`n===== USER SITE PACKAGES =====" -ForegroundColor Yellow
& $Py -c "import site; print(site.getusersitepackages()); print(site.getsitepackages())" 2>&1

Write-Host "`n===== DISTRIBUTION METADATA SEARCH =====" -ForegroundColor Yellow
Get-ChildItem -LiteralPath $Site -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '(?i)heretic' } |
    Select-Object FullName

Get-ChildItem -LiteralPath $Site -Directory -Filter "*.dist-info" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '(?i)heretic' } |
    Select-Object FullName

Get-ChildItem -LiteralPath $Site -Directory -Filter "*.egg-info" -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '(?i)heretic' } |
    Select-Object FullName

Write-Host "`n===== HERETIC SOURCE IDENTITY =====" -ForegroundColor Yellow

& $Py -c @"
import heretic
import inspect
import os

print("module:", heretic.__file__)
print("package:", os.path.dirname(heretic.__file__))

for name in ["config","main","model","system"]:
    try:
        m=__import__("heretic."+name,fromlist=["*"])
        print(name+":",m.__file__)
    except Exception as e:
        print(name+": IMPORT ERROR:",repr(e))
"@ 2>&1

Write-Host "`n===== CONFIG SCHEMA IDENTITY =====" -ForegroundColor Yellow

& $Py -c @"
import heretic.config as c
import inspect

print("config:",c.__file__)
print("symbols containing Config:")
print([x for x in dir(c) if "config" in x.lower() or "model" in x.lower()])

src=inspect.getsource(c)
for needle in ["model", "Field required", "Config"]:
    print("contains",repr(needle),needle in src)
"@ 2>&1

Write-Host "`n===== MAIN CLI IDENTITY =====" -ForegroundColor Yellow

& $Py -c @"
import heretic.main as m
import inspect

print("main:",m.__file__)
print("symbols:")
print([x for x in dir(m) if not x.startswith("_")][:100])

src=inspect.getsource(m)
print("main source length:",len(src))

for needle in ["--model","config.default.toml","v2.0.0","dev0"]:
    print("contains",repr(needle),needle in src)
"@ 2>&1

Write-Host "`n===== PYTHON PATH =====" -ForegroundColor Yellow
& $Py -c "import sys; print('--- sys.path ---'); [print(x) for x in sys.path]" 2>&1

Write-Host "`n===== PIP USER INSTALL RECORDS =====" -ForegroundColor Yellow
& $Py -m pip list --user 2>&1 |
    Select-String -Pattern "(?i)heretic|torch|transformers|accelerate|safetensors"

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "IDENTITY PROBE COMPLETE — NOTHING MODIFIED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
