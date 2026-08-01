param(
    [ValidateSet("list","inspect","run","snapshot")]
    [string]$Action = "list",
    [string]$Engine,
    [string]$Mode
)

$ErrorActionPreference = "Stop"

$manifestPath = "C:\Sovereign\Sovereign-EngineManifest.json"
$enginesRoot  = "C:\Sovereign\Engines"

if (-not (Test-Path $manifestPath)) {
    Write-Host "FATAL: Manifest not found at $manifestPath" -ForegroundColor Red
    exit 1
}

$manifestJson = Get-Content $manifestPath -Raw
$manifest     = $manifestJson | ConvertFrom-Json

function Get-EngineDef { param([string]$Name) return $manifest.engine_definitions.$Name }

function List-Engines {
    Write-Host "`n=== SOVEREIGN ENGINE REGISTRY ===`n" -ForegroundColor Cyan
    foreach ($name in $manifest.identity.engines) {
        $def = Get-EngineDef $name
        Write-Host ("- {0} : {1}" -f $name, $def.purpose)
    }
}

function Inspect-Engine {
    param([string]$Name)
    if (-not $Name) { Write-Host "Specify -Engine <name> for inspect." -ForegroundColor Yellow; exit 1 }
    $def = Get-EngineDef $Name
    if (-not $def) { Write-Host "Engine '$Name' not found in manifest." -ForegroundColor Red; exit 1 }

    Write-Host "`n=== ENGINE: $Name ===" -ForegroundColor Cyan
    Write-Host "Purpose: $($def.purpose)"
    if ($def.execution_flow) {
        Write-Host "`nExecution Flow:"; $def.execution_flow | ForEach-Object { Write-Host "  - $_" }
    }
    if ($def.modes) {
        Write-Host "`nModes:"
        $def.modes.PSObject.Properties.Name | ForEach-Object {
            $m = $_; $steps = $def.modes.$m -join ", "
            Write-Host "  - $m : $steps"
        }
    }
    if ($def.post_steps) {
        Write-Host "`nPost Steps:"; $def.post_steps | ForEach-Object { Write-Host "  - $_" }
    }
}

function Resolve-EngineScript {
    param([string]$Name)
    switch ($Name) {
        "HardenedEngine"       { return Join-Path $enginesRoot "Sovereign-HardenedEngine.ps1" }
        "ModularEngine"        { return Join-Path $enginesRoot "Sovereign-ModularEngine.ps1" }
        "Fusion2ScalExeEngine" { return Join-Path $enginesRoot "Sovereign-2ScalExeFusionEngine.ps1" }
        default { Write-Host "No script mapping for engine '$Name'." -ForegroundColor Red; exit 1 }
    }
}

function Run-Engine {
    param([string]$Name, [string]$Mode)
    if (-not $Name) { Write-Host "Specify -Engine <name> for run." -ForegroundColor Yellow; exit 1 }
    $def = Get-EngineDef $Name
    if (-not $def) { Write-Host "Engine '$Name' not found in manifest." -ForegroundColor Red; exit 1 }

    $scriptPath = Resolve-EngineScript $Name
    if (-not (Test-Path $scriptPath)) { Write-Host "Engine script not found at $scriptPath" -ForegroundColor Red; exit 1 }

    Write-Host "`n=== RUNNING ENGINE: $Name (Mode=$Mode) ===`n" -ForegroundColor Cyan
    if ($Name -eq "HardenedEngine") { & $scriptPath } else { if (-not $Mode) { $Mode = "full" }; & $scriptPath -Mode $Mode }
}

function Snapshot-State {
    $snapshot = [ordered]@{
        manifest_id = $manifest.sovereign_manifest
        stack_name  = $manifest.identity.stack_name
        timestamp   = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
        engines     = @()
        guarantees  = $manifest.sovereign_guarantees
        versions    = $manifest.versioning
    }

    foreach ($name in $manifest.identity.engines) {
        $def = Get-EngineDef $name
        $engineObj = [ordered]@{
            name      = $name
            purpose   = $def.purpose
            modes     = @()
            flow      = $def.execution_flow
            postSteps = $def.post_steps
        }
        if ($def.modes) {
            foreach ($m in $def.modes.PSObject.Properties.Name) {
                $engineObj.modes += [ordered]@{
                    name  = $m
                    steps = $def.modes.$m
                }
            }
        }
        $snapshot.engines += $engineObj
    }

    $json = $snapshot | ConvertTo-Json -Depth 6
    $outPath = "C:\Sovereign\Sovereign-EngineSnapshot.json"
    $json | Set-Content -Encoding UTF8 $outPath
    Write-Host "Snapshot written to $outPath" -ForegroundColor Green
}

switch ($Action) {
    "list"     { List-Engines }
    "inspect"  { Inspect-Engine -Name $Engine }
    "run"      { Run-Engine -Name $Engine -Mode $Mode }
    "snapshot" { Snapshot-State }
}
