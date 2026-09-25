# ============================================================
# AEGENTIX LIQUID MESH & SKYDIVE UNIFIED ORCHESTRATOR
# ============================================================

function Get-SkydivePortalStatus {
    try {
        $statusOut = wsl -e bash -l -c "skydive portal status 2>/dev/null"
        $isConnected = $statusOut -match "DESKTOP-HRUBG2T\s+\*\s+yes"
        $isGranted = $statusOut -match "AEGENTIX"
        return [PSCustomObject]@{
            Connected = $isConnected
            Granted   = $isGranted
            Raw       = ($statusOut -join "`n")
        }
    } catch {
        return [PSCustomObject]@{
            Connected = $false
            Granted   = $false
            Raw       = $_.Exception.Message
        }
    }
}

function Start-SkydivePortalSync {
    Write-Host "Syncing Skydive Portal for Agent AEGENTIX..." -ForegroundColor Cyan
    wsl -e bash -l -c "
        skydive portal daemon start 2>/dev/null || true
        skydive portal grant --agent AEGENTIX 2>/dev/null || true
        tmux has-session -t skydive-portal 2>/dev/null || tmux new-session -d -s skydive-portal 'skydive portal open --agent AEGENTIX --cwd /mnt/c/Users/eagle'
    "
    Start-Sleep -Seconds 2
    $portal = Get-SkydivePortalStatus
    if ($portal.Connected) {
        Write-Host "Skydive Portal: CONNECTED (Agent: AEGENTIX granted)" -ForegroundColor Green
    } else {
        Write-Host "Skydive Portal starting up..." -ForegroundColor Yellow
    }
}

function aegentix-mesh {
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host "  AEGENTIX LIQUID MESH - UNIFIED COMMAND NEXUS" -ForegroundColor Cyan
    Write-Host "==============================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # 1. Skydive Cloud Agent Status
    $portal = Get-SkydivePortalStatus
    Write-Host "[SKYDIVE CLOUD AGENT]" -ForegroundColor Magenta
    if ($portal.Connected -and $portal.Granted) {
        Write-Host "   Agent: AEGENTIX (Model: skydive/glide)" -ForegroundColor Gray
        Write-Host "   Portal Connection: LIVE AND CONNECTED" -ForegroundColor Green
        Write-Host "   Machine Access: DESKTOP-HRUBG2T (C:\Users\eagle)" -ForegroundColor Gray
    } else {
        Write-Host "   Portal Connection: Disconnected or Initializing" -ForegroundColor Yellow
        Write-Host "   Running auto-reconnect..." -ForegroundColor DarkYellow
        Start-SkydivePortalSync
    }
    Write-Host ""

    # 2. Local Cyberdeck Daemon and Local Swarm
    Write-Host "[LOCAL CYBERDECK AND DAEMON]" -ForegroundColor Cyan
    $job = Get-Job -Name "CyberdeckDaemon" -ErrorAction SilentlyContinue
    Write-Host "   Cyberdeck Daemon: $(if ($job -and $job.State -eq 'Running') { 'Active (Job ' + $job.Id + ')' } else { 'Inactive' })" -ForegroundColor Gray
    Write-Host "   Local Agents: agent-coding, agent-infra, agent-research, agent-security, agent-test" -ForegroundColor Gray
    Write-Host ""

    # 3. Cybercore Multi-Industry and OSINT Baking Engine
    Write-Host "[CYBERCORE BAKING ENGINE AND OSINT]" -ForegroundColor Green
    $bakingEngine = "C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\cybercore_baking_engine.py"
    if (Test-Path $bakingEngine) {
        Write-Host "   Engine Status: Available (cybercore_baking_engine.py)" -ForegroundColor Gray
        Write-Host "   Multi-Industry Bakes: Defense, Finance, Healthcare, Energy, Telecom, OSINT" -ForegroundColor Gray
        Write-Host "   AI Hygiene and Sanitization: Strict Policy Baked" -ForegroundColor Gray
    }
    Write-Host ""
    Write-Host "--------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "Quick Actions:" -ForegroundColor Yellow
    Write-Host "  aegentix-sync      : Re-establish live Skydive portal and permissions" -ForegroundColor White
    Write-Host "  cybercore-bake     : Run industry / OSINT bake matrix" -ForegroundColor White
    Write-Host "  skydive-chat       : Open interactive chat with AEGENTIX" -ForegroundColor White
    Write-Host "  cyber-status       : View Cyberdeck details" -ForegroundColor White
    Write-Host "--------------------------------------------------------------" -ForegroundColor DarkGray
}

function aegentix-sync {
    Start-SkydivePortalSync
}

function skydive-chat {
    skydive chat --agent AEGENTIX
}

function cybercore-bake {
    param([string]$Industry = "all")
    Write-Host "Initiating Cybercore Industry Bake: $Industry" -ForegroundColor Cyan
    python "C:\Users\eagle\AEGENTIX-CYBERNETICS-CORE\cybercore_baking_engine.py" --industry $Industry
}

# Export functions globally
Set-Alias mesh aegentix-mesh
