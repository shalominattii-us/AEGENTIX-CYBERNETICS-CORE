<#
    Sovereign Wrapper v4.0
    - Full Stage 6–12 orchestration
    - Node 24 + tsx stable
    - Self-healing dependency layer
    - Autonomous System v2.0 binding
#>

param(
    [ValidateSet('status','health','security','ai','test','build','docs','full')]
    [string]$Command = 'status',

    [switch]$Stage6,
    [switch]$Stage7,
    [switch]$Stage8,
    [switch]$Stage9,
    [switch]$Stage10,
    [switch]$Stage11,
    [switch]$Stage12
)

function Write-Stack {
    param([string]$Message,[string]$Level='INFO')
    Write-Host "[SOVEREIGN::$Level] $Message"
}

# ------------------------------------------------------------
# Repo Root Discovery
# ------------------------------------------------------------
function Get-RepoRoot {
    $start = Get-Location
    $current = $start

    while ($true) {
        $candidate = Join-Path $current "scripts\autonomous-system.ts"
        if (Test-Path $candidate) {
            return $current
        }

        $parent = Split-Path $current -Parent
        if ($parent -eq $current -or [string]::IsNullOrWhiteSpace($parent)) {
            throw "Repo root not found. autonomous-system.ts missing."
        }

        $current = $parent
    }
}

# ------------------------------------------------------------
# Self-Healing tsx + esbuild
# ------------------------------------------------------------
function Ensure-Tsx {
    try {
        $null = npx tsx --version 2>$null
        Write-Stack "tsx OK" "CHECK"
    } catch {
        Write-Stack "Installing tsx + esbuild" "ACTION"
        npm install tsx esbuild --save-dev
    }

    # Node 24 allowScripts fix
    Write-Stack "Approving esbuild install scripts" "ACTION"
    npm approve-scripts esbuild 2>$null

    Write-Stack "Re-running npm install" "ACTION"
    npm install
}

# ------------------------------------------------------------
# Autonomous System Binding
# ------------------------------------------------------------
function Invoke-AutonomousSystem {
    param(
        [ValidateSet('status','health','security','ai','test','build','docs','full')]
        [string]$Command = 'status'
    )

    if ([string]::IsNullOrWhiteSpace($Command)) {
        $Command = 'status'
    }

    $root = Get-RepoRoot
    Set-Location $root

    Write-Stack "Repo root: $root" "INFO"

    Ensure-Tsx

    $tsFile = Join-Path $root "scripts\autonomous-system.ts"
    if (-not (Test-Path $tsFile)) {
        Write-Stack "autonomous-system.ts missing at $tsFile" "ERROR"
        return
    }

    Write-Stack "Executing Autonomous System → $Command" "RUN"
    npx tsx $tsFile $Command
}

# ------------------------------------------------------------
# Stage Bindings
# ------------------------------------------------------------
function Invoke-Stage6  { Write-Stack "Stage 6 → HEALTH"   "MAP"; Invoke-AutonomousSystem -Command 'health' }
function Invoke-Stage7  { Write-Stack "Stage 7 → SECURITY" "MAP"; Invoke-AutonomousSystem -Command 'security' }
function Invoke-Stage8  { Write-Stack "Stage 8 → AI"       "MAP"; Invoke-AutonomousSystem -Command 'ai' }
function Invoke-Stage9  { Write-Stack "Stage 9 → TEST"     "MAP"; Invoke-AutonomousSystem -Command 'test' }
function Invoke-Stage10 { Write-Stack "Stage 10 → BUILD"   "MAP"; Invoke-AutonomousSystem -Command 'build' }
function Invoke-Stage11 { Write-Stack "Stage 11 → DOCS"    "MAP"; Invoke-AutonomousSystem -Command 'docs' }
function Invoke-Stage12 { Write-Stack "Stage 12 → FULL"    "MAP"; Invoke-AutonomousSystem -Command 'full' }

# ------------------------------------------------------------
# Orchestration Entry
# ------------------------------------------------------------
$stages = @(
    @{Flag=$Stage6;  Fn={Invoke-Stage6}},
    @{Flag=$Stage7;  Fn={Invoke-Stage7}},
    @{Flag=$Stage8;  Fn={Invoke-Stage8}},
    @{Flag=$Stage9;  Fn={Invoke-Stage9}},
    @{Flag=$Stage10; Fn={Invoke-Stage10}},
    @{Flag=$Stage11; Fn={Invoke-Stage11}},
    @{Flag=$Stage12; Fn={Invoke-Stage12}}
)

$selected = $stages | Where-Object { $_.Flag }

if ($selected.Count -gt 0) {
    foreach ($s in $selected) {
        & $s.Fn
    }
} else {
    Write-Stack "No stage switches → running command: $Command" "ENTRY"
    Invoke-AutonomousSystem -Command $Command
}
