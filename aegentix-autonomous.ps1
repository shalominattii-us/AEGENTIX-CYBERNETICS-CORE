# AEGENTIX AUTONOMOUS OPERATIONS
$ErrorActionPreference = 'Continue'
$ROOT = "C:\Aegentix"
$CYBERCORE = "http://localhost:7100"
$MODEL = "cybercore-tiny"
$LOGDIR = "$ROOT\.aegentix-logs"
$STATEFILE = "$ROOT\.aegentix-state.json"

Set-Location $ROOT
if (!(Test-Path $LOGDIR)) { New-Item -ItemType Directory -Path $LOGDIR -Force | Out-Null }

function Log {
    param([string]$Msg, [string]$Level = 'INFO')
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] [$Level] $Msg"
    Write-Host $line
    Add-Content -Path "$LOGDIR\aegentix-$(Get-Date -Format 'yyyy-MM-dd').log" -Value $line -ErrorAction SilentlyContinue
}

function State-Get {
    if (Test-Path $STATEFILE) {
        try { return Get-Content $STATEFILE -Raw | ConvertFrom-Json } catch {}
    }
    return @{ totalQueries = 0; totalErrors = 0; guardrailBlocks = 0 }
}

function State-Save($s) { $s | ConvertTo-Json -Depth 10 | Set-Content $STATEFILE -Encoding UTF8 }

function Test-CyberCore {
    try {
        $h = Invoke-RestMethod -Uri "$CYBERCORE/health" -TimeoutSec 5 -ErrorAction Stop
        return @{ ok = $true; data = $h }
    } catch { return @{ ok = $false; error = $_.Exception.Message } }
}

function Repair-CyberCore {
    Log "Self-heal: restarting CyberCore only" 'WARN'
    $target = "aegentix-cybercore-llm"
    $exists = docker ps -a --format "{{.Names}}" 2>$null | Where-Object { $_ -eq $target }
    if ($exists) {
        docker restart $target 2>&1 | Out-Null
        Log "Restarted: $target" 'INFO'
        Start-Sleep -Seconds 20
        return (Test-CyberCore).ok
    }
    Log "Container not found: $target" 'ERROR'
    return $false
}

function Invoke-CyberCore {
    param([string]$Prompt, [int]$Timeout = 60)
    $body = @{
        model = $MODEL
        messages = @( @{ role = 'user'; content = $Prompt } )
        stream = $false
    } | ConvertTo-Json -Depth 5 -Compress

    for ($i = 1; $i -le 2; $i++) {
        try {
            $r = Invoke-RestMethod -Uri "$CYBERCORE/v1/chat/completions" `
                -Method POST -ContentType 'application/json' `
                -Body $body -TimeoutSec $Timeout -ErrorAction Stop
            if ($r.choices[0].message.content) {
                return @{ ok = $true; text = $r.choices[0].message.content }
            }
            return @{ ok = $false; text = '[empty]' }
        } catch {
            $msg = $_.Exception.Message
            if ($msg -match '400|guardrail') {
                return @{ ok = $false; text = '[guardrail blocked]'; guardrail = $true }
            }
            Log "Attempt $i/2 failed: $msg" 'WARN'
            if ($i -lt 2) { Start-Sleep -Seconds 2 }
        }
    }
    return @{ ok = $false; text = '[failed]' }
}

# ---- MAIN ----
Clear-Host
Write-Host ""
Write-Host "  AEGENTIX AUTONOMOUS OPERATIONS" -ForegroundColor Cyan
Write-Host "  Self-Monitoring / Self-Healing" -ForegroundColor Gray
Write-Host ""

$state = State-Get
Log "Aegentix starting" 'INFO'

# Health
Write-Host "[1/3] Health check..." -ForegroundColor Yellow
$h = Test-CyberCore
if ($h.ok) {
    Write-Host "  OK - $($h.data.service)" -ForegroundColor Green
    Write-Host "  Models: $($h.data.models -join ', ')" -ForegroundColor Gray
} else {
    Write-Host "  FAIL: $($h.error)" -ForegroundColor Red
    Repair-CyberCore | Out-Null
}

# Warmup
Write-Host ""
Write-Host "[2/3] Warmup..." -ForegroundColor Yellow
$w = Invoke-CyberCore -Prompt "hi" -Timeout 60
if ($w.ok) { Write-Host "  Ready" -ForegroundColor Green }
else { Write-Host "  $($w.text)" -ForegroundColor Yellow }

# Loop
Write-Host ""
Write-Host "[3/3] ACTIVE" -ForegroundColor Yellow
Write-Host "  Commands: /health /heal /state /exit" -ForegroundColor DarkGray
Write-Host ""

while ($true) {
    Write-Host "Aegentix> " -NoNewline -ForegroundColor Cyan
    $inp = Read-Host
    if ([string]::IsNullOrWhiteSpace($inp)) { continue }

    switch -Regex ($inp) {
        '^/(exit|quit)$'  { State-Save $state; Write-Host "Bye." -ForegroundColor Green; return }
        '^/health$'       { $x = Test-CyberCore
                            if ($x.ok) { Write-Host "  ONLINE" -ForegroundColor Green }
                            else { Write-Host "  OFFLINE: $($x.error)" -ForegroundColor Red }
                            continue }
        '^/heal$'         { Repair-CyberCore | Out-Null; continue }
        '^/state$'        { Write-Host "  Queries: $($state.totalQueries)  Errors: $($state.totalErrors)  Blocks: $($state.guardrailBlocks)" -ForegroundColor Cyan; continue }
        '^/clear$'        { Clear-Host; continue }
    }

    Write-Host "  ..." -ForegroundColor DarkGray
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $r = Invoke-CyberCore -Prompt $inp
    $sw.Stop()
    $state.totalQueries++

    if ($r.ok) {
        Write-Host ""
        Write-Host "  $($r.text)" -ForegroundColor White
        Write-Host "  [$($sw.Elapsed.TotalSeconds.ToString('0.0'))s]" -ForegroundColor DarkGray
    } elseif ($r.guardrail) {
        $state.guardrailBlocks++
        Write-Host "  Guardrail blocked" -ForegroundColor Yellow
    } else {
        $state.totalErrors++
        Write-Host "  $($r.text)" -ForegroundColor Red
    }
    Write-Host ""
    State-Save $state
}
