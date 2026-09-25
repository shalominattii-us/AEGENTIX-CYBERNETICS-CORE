# ============================================================
# SOVEREIGN NANOTX EMITTER — Universal agent compute ledger
# HEMPEROR EDITION — MCP Sovereign Runtime
# ============================================================
# Every agent action emits a nanotransaction.
# Every compute becomes ledger-anchored.
# The system is the ledger. The ledger is the system.

function _guid { return [System.Guid]::NewGuid().ToString() }
function _coalescing { param([object]$Value, [object]$Default) if ($null -ne $Value) { return $Value } return $Default }

$Global:NanoLedgerPath = Join-Path $PSScriptRoot "system_nano_ledger.jsonl"

# ============================================================
# 1 — UNIVERSAL NANOTX EMITTER
# ============================================================

function Invoke-NanoTx {
    [CmdletBinding()]
    param(
        [string]$Agent,
        [string]$Action,
        [psobject]$Payload,
        [psobject]$Result,
        [double]$IntegrityScore = 0.99,
        [double]$RewardAmount = 1.0,
        [string]$RewardToken = "EOC",
        [double]$StakeRatio = 0.15,
        [string]$Network = "mainnet",
        [string]$Source = "mcp-system"
    )

    $guid = [System.Guid]::NewGuid().ToString()
    $packet = @{
        worker_id       = $Agent
        compute_task    = $Action
        integrity_score = $IntegrityScore
        reward_amount   = $RewardAmount
        reward_token    = $RewardToken
        stake_ratio     = $StakeRatio
        network         = $Network
        memory_id       = $guid
        source          = $Source
        timestamp       = (Get-Date).ToString("o")
        payload_size    = if ($Payload) { ($Payload | ConvertTo-Json -Depth 5).Length } else { 0 }
        result_size     = if ($Result) { ($Result | ConvertTo-Json -Depth 5).Length } else { 0 }
    }

    $json = $packet | ConvertTo-Json -Depth 10 -Compress

    # Emit to EOC staking API
    $apiResult = $null
    $apiStatus = "emitted"
    try {
        $apiResult = Invoke-RestMethod `
            -Method POST `
            -Uri "http://localhost:5001/api/eoc/stake" `
            -Body $json `
            -ContentType "application/json" `
            -TimeoutSec 10
        $apiStatus = $apiResult.status
    } catch {
        $apiStatus = "api-unreachable"
    }

    # Ledger entry (local + API reference)
    $ledgerEntry = @{
        packet_id       = _coalescing $apiResult.packetId ([System.Guid]::NewGuid().ToString())
        worker_id       = $Agent
        compute_task    = $Action
        integrity_score = $IntegrityScore
        reward_amount   = $RewardAmount
        reward_token    = $RewardToken
        stake_ratio     = $StakeRatio
        network         = $Network
        memory_id       = $packet.memory_id
        source          = $Source
        timestamp       = $packet.timestamp
        api_status      = $apiStatus
        consensus       = _coalescing $apiResult.consensus 0
        eoc_ledger_entry= _coalescing $apiResult.eocLedgerEntry ""
        payload_size    = $packet.payload_size
        result_size     = $packet.result_size
    }

    # Append to local ledger (JSONL — single line per entry)
    ($ledgerEntry | ConvertTo-Json -Depth 10 -Compress) + "`n" | Add-Content -Path $Global:NanoLedgerPath -Encoding UTF8

    return $ledgerEntry
}

# ============================================================
# 2 — AGENT-LEVEL WRAPPER
# Wraps every subordinate agent action in a nanotx
# ============================================================

function Invoke-AgentAction {
    [CmdletBinding()]
    param(
        [string]$AgentName,
        [string]$Action,
        [scriptblock]$Execute,
        [double]$IntegrityOverride = -1.0
    )

    $startTime = Get-Date
    $integrity = if ($IntegrityOverride -ge 0) { $IntegrityOverride } else { 0.99 }

    try {
        $result = & $Execute

        Invoke-NanoTx `
            -Agent $AgentName `
            -Action $Action `
            -Payload @{ action = $Action; agent = $AgentName; started = $startTime.ToString("o") } `
            -Result $result `
            -IntegrityScore $integrity `
            -RewardAmount (Get-ActionReward -Action $Action -Agent $AgentName)

        return $result
    } catch {
        Invoke-NanoTx `
            -Agent $AgentName `
            -Action $Action `
            -Payload @{ action = $Action; agent = $AgentName; started = $startTime.ToString("o"); error = $_.Exception.Message } `
            -Result @{ status = "failed"; error = $_.Exception.Message } `
            -IntegrityScore 0.5 `
            -RewardAmount 0.1

        throw
    }
}

# ============================================================
# 3 — SUPER-AGENT WRAPPER
# Wraps executive decisions in a nanotx
# ============================================================

function Invoke-SuperAgent {
    [CmdletBinding()]
    param(
        [string]$SuperAgent,
        [string]$Intent,
        [scriptblock]$Resolve,
        [psobject]$Context
    )

    $startTime = Get-Date

    try {
        $result = & $Resolve -Context $Context

        Invoke-NanoTx `
            -Agent $SuperAgent `
            -Action $Intent `
            -Payload $Context `
            -Result $result `
            -IntegrityScore 0.999 `
            -RewardAmount (Get-SuperAgentReward -SuperAgent $SuperAgent -Intent $Intent)

        return $result
    } catch {
        Invoke-NanoTx `
            -Agent $SuperAgent `
            -Action $Intent `
            -Payload $Context `
            -Result @{ status = "failed"; error = $_.Exception.Message } `
            -IntegrityScore 0.5 `
            -RewardAmount 0.5

        throw
    }
}

# ============================================================
# 4 — SYSTEM HEARTBEAT
# ============================================================

function Send-SystemHeartbeat {
    param(
        [string]$Agent = "Aegentix",
        [string]$Component = "sovereign-mcp"
    )

    $proc = [System.Diagnostics.Process]::GetCurrentProcess()
    $uptime = (Get-Date) - $proc.StartTime
    $uptimeSeconds = [math]::Round($uptime.TotalSeconds, 1)

    Invoke-NanoTx `
        -Agent $Agent `
        -Action "heartbeat" `
        -Payload @{ uptime_seconds = $uptimeSeconds; component = $Component; timestamp = (Get-Date).ToString("o") } `
        -Result @{ status = "ok"; uptime_seconds = $uptimeSeconds } `
        -IntegrityScore 1.0 `
        -RewardAmount 0.05 `
        -Source "system-heartbeat"
}

# ============================================================
# 5 — TASK ROUTING NANOTX
# ============================================================

function Route-Task {
    [CmdletBinding()]
    param(
        [psobject]$Task,
        [scriptblock]$SelectAgent
    )

    $selectedAgent = & $SelectAgent -Task $Task
    $taskType = if ($Task.action) { $Task.action } else { $Task.GetType().Name }

    Invoke-NanoTx `
        -Agent "Aegentix" `
        -Action "route_task" `
        -Payload $Task `
        -Result @{ selected_agent = $selectedAgent; task_type = $taskType } `
        -IntegrityScore 0.99 `
        -RewardAmount 0.2 `
        -Source "task-router"

    return $selectedAgent
}

# ============================================================
# 6 — VOICE SYNTHESIS NANOTX
# Wraps every voice output in a nanotx
# ============================================================

function Emit-VoiceNanotx {
    [CmdletBinding()]
    param(
        [string]$Agent,
        [string]$VoiceModel,
        [string]$Text,
        [string]$OutputPath,
        [string]$ContextAction = "voice-synthesis"
    )

    $audioBytes = 0
    if (Test-Path $OutputPath) {
        $audioBytes = (Get-Item $OutputPath).Length
    }

    $reward = [math]::Max(0.5, [math]::Round($audioBytes / 1024.0 / 10.0, 2))

    Invoke-NanoTx `
        -Agent $Agent `
        -Action $ContextAction `
        -Payload @{
            voice_model = $VoiceModel
            text_length = $Text.Length
            context_action = $ContextAction
            agent = $Agent
        } `
        -Result @{
            output_path = $OutputPath
            audio_bytes = $audioBytes
            text_length = $Text.Length
            voice_model = $VoiceModel
            status = if (Test-Path $OutputPath) { "synthesized" } else { "failed" }
        } `
        -IntegrityScore 0.99 `
        -RewardAmount $reward `
        -Source "voice-stack"
}

# ============================================================
# 7 — MEMORY WRITE NANOTX
# Wraps every shared memory write in a nanotx
# ============================================================

function Emit-MemoryNanotx {
    [CmdletBinding()]
    param(
        [string]$Agent,
        [string]$MemoryPath,
        [string]$Action,
        [string]$ContentRef
    )

    Invoke-NanoTx `
        -Agent $Agent `
        -Action "memory-write" `
        -Payload @{
            memory_path = $MemoryPath
            action = $Action
            content_ref = $ContentRef
            agent = $Agent
        } `
        -Result @{
            memory_path = $MemoryPath
            action = $Action
            content_ref = $ContentRef
            status = "written"
        } `
        -IntegrityScore 0.995 `
        -RewardAmount 0.3 `
        -Source "memory-layer"
}

# ============================================================
# 8 — PERSONA SWITCH NANOTX
# Wraps every voice identity switch in a nanotx
# ============================================================

function Emit-PersonaSwitchNanotx {
    [CmdletBinding()]
    param(
        [string]$Agent,
        [string]$FromPersona,
        [string]$ToPersona,
        [string]$Reason
    )

    Invoke-NanoTx `
        -Agent $Agent `
        -Action "persona-switch" `
        -Payload @{
            from_persona = $FromPersona
            to_persona   = $ToPersona
            reason        = $Reason
            agent         = $Agent
        } `
        -Result @{
            from_persona = $FromPersona
            to_persona   = $ToPersona
            reason        = $Reason
            status        = "switched"
        } `
        -IntegrityScore 0.99 `
        -RewardAmount 0.25 `
        -Source "persona-firewall"
}

# ============================================================
# 9 — DELEGATION NANOTX
# Wraps every agent delegation in a nanotx
# ============================================================

function Emit-DelegationNanotx {
    [CmdletBinding()]
    param(
        [string]$Delegator,
        [string]$Delegatee,
        [string]$Task,
        [psobject]$Payload
    )

    Invoke-NanoTx `
        -Agent $Delegator `
        -Action "delegation" `
        -Payload @{
            delegator = $Delegator
            delegatee = $Delegatee
            task      = $Task
            payload   = $Payload
        } `
        -Result @{
            delegator = $Delegator
            delegatee = $Delegatee
            task      = $Task
            status    = "delegated"
        } `
        -IntegrityScore 0.99 `
        -RewardAmount 0.5 `
        -Source "delegation-layer"
}

# ============================================================
# 10 — REWARD CALCULATORS
# ============================================================

function Get-ActionReward {
    param([string]$Action, [string]$Agent)

    $base = switch ($Action) {
        "voice-synthesis"   { 1.0 }
        "intent-derivation" { 0.3 }
        "persona-check"     { 0.3 }
        "memory-write"      { 0.3 }
        "route_task"        { 0.2 }
        default             { 0.5 }
    }
    return $base
}

function Get-SuperAgentReward {
    param([string]$SuperAgent, [string]$Intent)

    $base = switch ($Intent) {
        "status"          { 1.0 }
        "explain"         { 1.5 }
        "system-failure"  { 3.0 }
        "alert"           { 2.0 }
        "delegation"      { 2.0 }
        "planning"        { 2.5 }
        default           { 1.0 }
    }
    return $base
}

# ============================================================
# 11 — LEDGER QUERY
# ============================================================

function Get-NanoLedger {
    param(
        [string]$Agent,
        [int]$Limit = 50,
        [string]$Since
    )

    if (-not (Test-Path $Global:NanoLedgerPath)) {
        return @()
    }

    $entriesRaw = Get-Content $Global:NanoLedgerPath -Encoding UTF8 -Raw
    if ([string]::IsNullOrWhiteSpace($entriesRaw)) { return @() }

    $entryStrings = $entriesRaw -split "`r?`n" | Where-Object { $_ -match "^\s*\{" }
    $entries = @()
    foreach ($line in $entryStrings) {
        try {
            $entries += $line | ConvertFrom-Json
        } catch {
            # skip malformed lines
        }
    }

    if ($Agent) {
        $entries = $entries | Where-Object { $_.worker_id -eq $Agent }
    }

    if ($Since) {
        $entries = $entries | Where-Object { [datetime]$_.timestamp -gt [datetime]$Since }
    }

    return $entries | Select-Object -Last $Limit
}

function Get-NanoLedgerStats {
    param([string]$Agent)

    if (-not (Test-Path $Global:NanoLedgerPath)) {
        return @{ total_actions = 0; total_reward = 0; total_bytes = 0; by_agent = @{}; by_action = @{} }
    }

    $entriesRaw = Get-Content $Global:NanoLedgerPath -Encoding UTF8 -Raw
    if ([string]::IsNullOrWhiteSpace($entriesRaw)) {
        return @{ total_actions = 0; total_reward = 0.0; total_bytes = 0; by_agent = @{}; by_action = @{} }
    }

    $entryStrings = $entriesRaw -split "`r?`n" | Where-Object { $_ -match "^\s*\{" }
    $entries = @()
    foreach ($line in $entryStrings) {
        try {
            $entries += $line | ConvertFrom-Json
        } catch {
            # skip malformed lines
        }
    }

    $totalActions = 0
    $totalReward = 0.0
    $totalBytes = 0
    $byAgent = @{}
    $byAction = @{}

    foreach ($e in $entries) {
        $totalActions++
        $totalReward += [double]$e.reward_amount
        $totalBytes += [int]$e.payload_size + [int]$e.result_size

        $agentKey = if ($e.worker_id) { $e.worker_id } else { "unknown" }
        if (-not $byAgent.ContainsKey($agentKey)) {
            $byAgent[$agentKey] = @{ count = 0; reward = 0.0 }
        }
        $byAgent[$agentKey].count++
        $byAgent[$agentKey].reward += [double]$e.reward_amount

        $actionKey = if ($e.compute_task) { $e.compute_task } else { "unknown" }
        if (-not $byAction.ContainsKey($actionKey)) {
            $byAction[$actionKey] = @{ count = 0; reward = 0.0 }
        }
        $byAction[$actionKey].count++
        $byAction[$actionKey].reward += [double]$e.reward_amount
    }

    return @{
        total_actions = $totalActions
        total_reward  = [math]::Round($totalReward, 2)
        total_bytes   = $totalBytes
        by_agent      = $byAgent
        by_action     = $byAction
    }
}

# ============================================================
# 12 — SYSTEM INITIALIZATION
# ============================================================

function Initialize-NanoTxSystem {
    param(
        [string]$LedgerPath = $null
    )

    if ($LedgerPath) {
        $Global:NanoLedgerPath = $LedgerPath
    }

    $dir = Split-Path $Global:NanoLedgerPath -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }

    if (-not (Test-Path $Global:NanoLedgerPath)) {
        Set-Content -Path $Global:NanoLedgerPath -Value "" -Encoding UTF8 -Force
    }

    Send-SystemHeartbeat -Component "mcp-initialization"

    Write-Host "Sovereign Nanotransaction System initialized."
    Write-Host "Ledger: $Global:NanoLedgerPath"
    Write-Host "API:    http://localhost:5001/api/eoc/stake"
    Write-Host ""
    Write-Host "MCP Sovereign Runtime active -- every agent action is now a nanotransaction."
}

# ============================================================
# EXPORTS
# ============================================================

Export-ModuleMember `
    -Function @(`
        "Invoke-NanoTx",
        "Invoke-AgentAction",
        "Invoke-SuperAgent",
        "Send-SystemHeartbeat",
        "Route-Task",
        "Emit-VoiceNanotx",
        "Emit-MemoryNanotx",
        "Emit-PersonaSwitchNanotx",
        "Emit-DelegationNanotx",
        "Get-NanoLedger",
        "Get-NanoLedgerStats",
        "Initialize-NanoTxSystem"
    )
