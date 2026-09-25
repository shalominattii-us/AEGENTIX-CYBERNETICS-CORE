$ErrorActionPreference = "SilentlyContinue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "AEGENTIX — FIND TRANSFORMERS MODEL DIRECTORIES" -ForegroundColor Cyan
Write-Host "READ-ONLY" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$Roots = @(
    "$env:USERPROFILE\.cache\huggingface\hub",
    "$env:USERPROFILE",
    "C:\Aegentix",
    "G:\"
)

$Found = [System.Collections.Generic.List[object]]::new()

foreach ($Root in $Roots) {
    if (-not (Test-Path -LiteralPath $Root)) { continue }

    Write-Host "Scanning: $Root" -ForegroundColor DarkGray

    Get-ChildItem -LiteralPath $Root -Recurse -File -Filter "config.json" -ErrorAction SilentlyContinue |
        ForEach-Object {
            $Dir = $_.Directory.FullName

            $Weights = @(
                Get-ChildItem -LiteralPath $Dir -File -ErrorAction SilentlyContinue |
                    Where-Object {
                        $_.Extension -in @(".safetensors",".bin",".pt",".pth") -and
                        $_.Length -gt 1048576
                    }
            )

            if ($Weights.Count -gt 0) {
                try {
                    $Cfg = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json

                    $Found.Add([PSCustomObject]@{
                        ModelType = $Cfg.model_type
                        Architecture = (($Cfg.architectures -join ", "))
                        WeightFiles = $Weights.Count
                        WeightGB = [math]::Round((($Weights | Measure-Object Length -Sum).Sum / 1GB),3)
                        Config = $_.FullName
                    })
                }
                catch {}
            }
        }
}

$Found = $Found |
    Sort-Object Config -Unique |
    Sort-Object WeightGB -Descending

Write-Host ""
Write-Host "TRANSFORMERS CANDIDATES: $($Found.Count)" -ForegroundColor Green

if ($Found.Count -eq 0) {
    Write-Host "NO COMPLETE TRANSFORMERS MODEL DIRECTORIES FOUND." -ForegroundColor Yellow
}
else {
    foreach ($M in $Found) {
        Write-Host ""
        Write-Host "MODEL TYPE : $($M.ModelType)" -ForegroundColor Green
        Write-Host "ARCH       : $($M.Architecture)"
        Write-Host "WEIGHTS    : $($M.WeightFiles) files / $($M.WeightGB) GB"
        Write-Host "CONFIG     : $($M.Config)" -ForegroundColor Cyan
    }
}

$Out = "C:\Aegentix\HERETIC-TRANSFORMERS-CANDIDATES.txt"

$Found |
    Format-Table -AutoSize |
    Out-String |
    Set-Content -LiteralPath $Out -Encoding UTF8

Write-Host ""
Write-Host "REPORT: $Out" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Green
