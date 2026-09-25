$ErrorActionPreference = "Continue"

$Out = "C:\Aegentix\HERETIC-MODEL-INVENTORY.txt"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AEGENTIX — HERETIC MODEL INVENTORY" -ForegroundColor Cyan
Write-Host "READ-ONLY — NO DOWNLOADS / NO CHANGES" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$Results = [System.Collections.Generic.List[object]]::new()

$Roots = @(
    "$env:USERPROFILE\.cache\huggingface\hub",
    "C:\Aegentix",
    "C:\Users\eagle",
    "D:\",
    "E:\",
    "F:\",
    "G:\"
)

$Extensions = @(
    "*.safetensors",
    "*.bin",
    "*.pt",
    "*.pth",
    "*.gguf"
)

Write-Host "`n[1/3] Searching for model files..." -ForegroundColor Yellow

foreach ($Root in $Roots) {
    if (-not (Test-Path -LiteralPath $Root)) {
        continue
    }

    Write-Host "Scanning: $Root" -ForegroundColor DarkGray

    foreach ($Ext in $Extensions) {
        try {
            Get-ChildItem -LiteralPath $Root -Recurse -File -Filter $Ext -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $Results.Add([PSCustomObject]@{
                        Type = $_.Extension
                        SizeGB = [math]::Round($_.Length / 1GB, 3)
                        SizeMB = [math]::Round($_.Length / 1MB, 1)
                        Path = $_.FullName
                    })
                }
        }
        catch {}
    }
}

$Results = $Results |
    Sort-Object Path -Unique |
    Sort-Object SizeGB -Descending

Write-Host "`n[2/3] Model files found: $($Results.Count)" -ForegroundColor Green

if ($Results.Count -eq 0) {
    Write-Host "NO MODEL FILES FOUND." -ForegroundColor Red
}
else {
    foreach ($R in $Results) {
        Write-Host ("{0,-12} {1,8} GB  {2}" -f $R.Type,$R.SizeGB,$R.Path)
    }
}

Write-Host "`n[3/3] Checking Hugging Face snapshots..." -ForegroundColor Yellow

$Snapshots = @()

$HFRoot = "$env:USERPROFILE\.cache\huggingface\hub"

if (Test-Path -LiteralPath $HFRoot) {
    $Snapshots = Get-ChildItem -LiteralPath $HFRoot -Directory -Recurse -ErrorAction SilentlyContinue |
        Where-Object {
            $_.FullName -match '\\snapshots\\[0-9a-f]{40}$'
        }
}

if ($Snapshots.Count -eq 0) {
    Write-Host "No Hugging Face snapshots found." -ForegroundColor Yellow
}
else {
    foreach ($S in $Snapshots) {
        $Files = @(Get-ChildItem -LiteralPath $S.FullName -File -ErrorAction SilentlyContinue)
        $Bytes = ($Files | Measure-Object -Property Length -Sum).Sum

        if ($null -eq $Bytes) {
            $Bytes = 0
        }

        $GB = [math]::Round($Bytes / 1GB, 3)

        if ($Bytes -gt 0) {
            $Status = "USABLE-DATA-PRESENT"
        }
        else {
            $Status = "EMPTY-OR-HOLLOW"
        }

        Write-Host ("{0} | files={1} | {2} GB | {3}" -f $Status,$Files.Count,$GB,$S.FullName)
    }
}

"`r`n============================================================" | Set-Content -LiteralPath $Out -Encoding UTF8
"AEGENTIX HERETIC MODEL INVENTORY" | Add-Content -LiteralPath $Out
"Generated: $(Get-Date -Format s)" | Add-Content -LiteralPath $Out
"============================================================" | Add-Content -LiteralPath $Out

foreach ($R in $Results) {
    ("{0}`t{1} GB`t{2}" -f $R.Type,$R.SizeGB,$R.Path) |
        Add-Content -LiteralPath $Out
}

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "INVENTORY COMPLETE" -ForegroundColor Green
Write-Host "REPORT: $Out" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
