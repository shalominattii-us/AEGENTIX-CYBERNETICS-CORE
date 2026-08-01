Write-Host "`n=== SOVEREIGN META-ACTIVATION vΩ ===`n" -ForegroundColor Magenta

$root = "C:\Sovereign"

$required = @(
    "Sovereign-EngineManifest.json",
    "Sovereign-MetaArtifact.sovmeta",
    "Sovereign-MetaInterpreter.ps1",
    "Sovereign-LRV.ps1",
    "Core\Sovereign-Core.ps1",
    "Engines\Sovereign-HardenedEngine.ps1",
    "Engines\Sovereign-ModularEngine.ps1",
    "Engines\Sovereign-2ScalExeFusionEngine.ps1"
)

foreach ($file in $required) {
    $path = Join-Path $root $file
    if (-not (Test-Path $path)) {
        Write-Host "MISSING: $file" -ForegroundColor Red
        Write-Host "Activation aborted." -ForegroundColor Red
        exit 1
    }
}

Write-Host "All Sovereign components located." -ForegroundColor Green

$metaInterpreter = Join-Path $root "Sovereign-MetaInterpreter.ps1"

Write-Host "Binding Meta-Interpreter..." -ForegroundColor Yellow
. $metaInterpreter
Write-Host "Meta-Interpreter bound." -ForegroundColor Green

Write-Host "`nDescribing Sovereign Stack..." -ForegroundColor Yellow
& $metaInterpreter -Action describe

Write-Host "`nGenerating Sovereign Snapshot..." -ForegroundColor Yellow
& $metaInterpreter -Action timeline
& (Join-Path $root "Sovereign-LRV.ps1") -Action snapshot

Write-Host "`nSnapshot generated." -ForegroundColor Green

Write-Host "`nExecuting Hardened Engine (default activation)..." -ForegroundColor Yellow
& (Join-Path $root "Sovereign-LRV.ps1") -Action run -Engine HardenedEngine

Write-Host "`n=== SOVEREIGN META-ACTIVATION COMPLETE ===" -ForegroundColor Magenta
Write-Host "System is now META-ATOMIC READY." -ForegroundColor Cyan
