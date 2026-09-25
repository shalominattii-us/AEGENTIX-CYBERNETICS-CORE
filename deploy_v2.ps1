<#
.SYNOPSIS
    Aegentix Studio deployment for DESKTOP-HRUBG2T / ROG Ally Z2
    Installs JetBrains IDE + CyberCore plugin config + Gym stack
#>

$ErrorActionPreference = "Continue"
$AEGENTIX_ROOT = "C:\Aegentix"
$LOG = "C:\Aegentix\deploy_log.txt"

function Log($msg) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $line
    Add-Content -Path $LOG -Value $line
}

Log "=== AEGENTIX STUDIO DEPLOYMENT START ==="

# ── 1. Hardware detection ─────────────────────────────────────────────
$cpu = (Get-CimInstance Win32_Processor).Name
$gpu = (Get-CimInstance Win32_VideoController).Name -join " | "
Log "CPU: $cpu"
Log "GPU: $gpu"
$hasNvidia = ($gpu -match "NVIDIA")
$hasAMD = ($gpu -match "AMD|Radeon")
Log "Nvidia detected: $hasNvidia | AMD detected: $hasAMD"

# ── 2. Install JetBrains PyCharm Community ────────────────────────────
$pycharmInstalled = Test-Path "$env:LOCALAPPDATA\Programs\PyCharm Community Edition"
if (-not $pycharmInstalled) {
    Log "Installing PyCharm Community via winget..."
    try {
        winget install -e --id JetBrains.PyCharm.Community --silent --accept-package-agreements --disable-interactivity | Out-Null
        Log "PyCharm install initiated"
    } catch {
        Log "winget failed: $($_.Exception.Message)"
    }
} else {
    Log "PyCharm already present"
}

# ── 3. Clone Gym repo ─────────────────────────────────────────────────
$gymDir = "$AEGENTIX_ROOT\cybergennet"
if (-not (Test-Path $gymDir)) {
    Log "Cloning CyberGenetic Gym..."
    git clone https://github.com/shalominattii-us/cybergennet-gym.git $gymDir 2>&1 | Out-Null
    Log "Gym cloned"
} else {
    Log "Gym already present, pulling..."
    Push-Location $gymDir
    git pull 2>&1 | Out-Null
    Pop-Location
}

# ── 4. Python venv + deps ─────────────────────────────────────────────
if (Test-Path $gymDir) {
    $venv = "$gymDir\.venv"
    if (-not (Test-Path "$venv\Scripts\python.exe")) {
        Log "Creating venv..."
        python -m venv $venv 2>&1 | Out-Null
    }
    if (Test-Path "$venv\Scripts\python.exe") {
        Log "Installing Gym dependencies..."
        & "$venv\Scripts\pip.exe" install --upgrade pip --quiet 2>&1 | Out-Null
        & "$venv\Scripts\pip.exe" install -e "$gymDir[dev]" --quiet 2>&1 | Out-Null
        Log "Dependencies installed"
    }
}

# ── 5. CyberCore plugin config for JetBrains ──────────────────────────
$jbRoot = Join-Path $env:APPDATA "JetBrains"
$pluginTarget = "$AEGENTIX_ROOT\aegentix-plugin"
New-Item -ItemType Directory -Path $pluginTarget -Force | Out-Null

$config = @{
    llm = @{
        endpoint = "http://localhost:7100"
        model = "cybercore-core"
        backend = "auto"
        temperature = 0.3
        max_tokens = 4096
    }
    gym = @{
        endpoint = "http://localhost:3001/api/v1"
    }
    aegentix = @{
        root = $AEGENTIX_ROOT
    }
    hardware = @{
        cpu = $cpu
        gpu = $gpu
        nvidia = $hasNvidia
        amd = $hasAMD
    }
} | ConvertTo-Json -Depth 4

Set-Content -Path "$pluginTarget\config.json" -Value $config -Encoding UTF8
Log "CyberCore plugin config written to $pluginTarget\config.json"

# ── 6. Try starting the Gym to verify ─────────────────────────────────
$started = $false
if (Test-Path "$gymDir\.venv\Scripts\python.exe") {
    Log "Starting Gym server for verification..."
    $gymProc = Start-Process -FilePath "$gymDir\.venv\Scripts\python.exe" `
        -ArgumentList "-m","uvicorn","apps.api.main:app","--host","0.0.0.0","--port","3001" `
        -WorkingDirectory $gymDir `
        -WindowStyle Hidden `
        -PassThru
    Start-Sleep -Seconds 12
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:3001/health" -UseBasicParsing -TimeoutSec 5
        Log "Gym health check: $($resp.StatusCode)"
        $started = $true
    } catch {
        Log "Gym health check failed: $($_.Exception.Message)"
    }
    if ($started) {
        Log "Gym is RUNNING at http://localhost:3001"
    } else {
        Log "Gym did not start — check log"
    }
}

Log "=== DEPLOYMENT COMPLETE ==="
Log "Next: open PyCharm, import $gymDir, enable plugin from $pluginTarget"