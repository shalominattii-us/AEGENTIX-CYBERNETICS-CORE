# ============================================================
# AEGENTIX SOVEREIGN CORE
# MCP Nanotransaction + Agent Mesh + Captain Kirk Voice
# ============================================================

# =========================
# GLOBAL CONFIG
# =========================
$Global:AegentixConfig = @{
    ApiBaseUrl        = "http://localhost:5001/api/eoc"
    DefaultNetwork    = "mainnet"
    DefaultStakeRatio = 0.15
    DefaultRewardToken = "EOC"
    LedgerPath        = Join-Path $PSScriptRoot "aegentix_nano_ledger.jsonl"
}

# =========================
# CORE NANOTX EMITTER
# =========================
function Invoke-NanoTx {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]  $Agent,
        [Parameter(Mandatory)][string]  $Action,
        [Parameter(Mandatory)][psobject]$Payload,
        [Parameter(Mandatory)][psobject]$Result,
        [Parameter()][double]          $IntegrityScore = 0.99,
        [Parameter()][double]          $RewardAmount   = 1.0,
        [Parameter()][string]          $RewardToken    = $Global:AegentixConfig.DefaultRewardToken,
        [Parameter()][double]          $StakeRatio     = $Global:AegentixConfig.DefaultStakeRatio,
        [Parameter()][string]          $Network        = $Global:AegentixConfig.DefaultNetwork,
        [Parameter()][string]          $Source         = "aegentix-mcp"
    )

    $packet = [pscustomobject]@{
        worker_id       = $Agent
        compute_task    = $Action
        integrity_score = $IntegrityScore
        reward_amount   = $RewardAmount
        reward_token    = $RewardToken
        stake_ratio     = $StakeRatio
        network         = $Network
        memory_id       = [guid]::NewGuid().ToString()
        source          = $Source
        timestamp       = (Get-Date).ToString("o")
    }

    $json = $packet | ConvertTo-Json -Depth 10

    $url = "$($Global:AegentixConfig.ApiBaseUrl)/stake"
    $response = $null
    $apiStatus = "emitted"
    try {
        $response = Invoke-RestMethod -Method POST -Uri $url -Body $json -ContentType "application/json" -TimeoutSec 10
        $apiStatus = $response.status
    } catch {
        $apiStatus = "api-unreachable"
    }

    $packetId = if ($null -ne $response.packetId) { $response.packetId } else { [guid]::NewGuid().ToString() }
    $consensus = if ($null -ne $response.consensus) { $response.consensus } else { 0 }
    $eocEntry = if ($null -ne $response.eocLedgerEntry) { $response.eocLedgerEntry } else { "" }

    $entry = [pscustomobject]@{
        timestamp          = (Get-Date).ToString("o")
        packet_id          = $packetId
        worker_id          = $Agent
        compute_task       = $Action
        integrity_score    = $IntegrityScore
        reward_amount      = $RewardAmount
        reward_token       = $RewardToken
        stake_ratio        = $StakeRatio
        network            = $Network
        memory_id          = $packet.memory_id
        source             = $Source
        api_status         = $apiStatus
        consensus          = $consensus
        eoc_ledger_entry   = $eocEntry
    }

    ($entry | ConvertTo-Json -Depth 10) + "`n" | Add-Content -Path $Global:AegentixConfig.LedgerPath -Encoding UTF8

    return $entry
}

function Get-NanoStatus {
    [CmdletBinding()]
    param()

    $url = "$($Global:AegentixConfig.ApiBaseUrl)/status"
    try {
        return Invoke-RestMethod -Method GET -Uri $url -TimeoutSec 5
    } catch {
        return @{ status = "api-unreachable"; error = $_.Exception.Message }
    }
}

# =========================
# AGENT WRAPPERS
# =========================
function Invoke-AgentAction {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]     $AgentName,
        [Parameter(Mandatory)][string]     $ActionName,
        [Parameter()][hashtable]           $Payload = @{},
        [Parameter()][scriptblock]         $ActionBlock
    )

    if (-not $ActionBlock) {
        throw "ActionBlock is required for Invoke-AgentAction."
    }

    $result = & $ActionBlock $Payload

    $nano = Invoke-NanoTx `
        -Agent  $AgentName `
        -Action $ActionName `
        -Payload ([pscustomobject]$Payload) `
        -Result  $result

    return $result
}

function Invoke-SuperAgent {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]    $SuperAgent,
        [Parameter(Mandatory)][string]    $Intent,
        [Parameter()][hashtable]          $Context = @{},
        [Parameter()][scriptblock]        $IntentBlock
    )

    if (-not $IntentBlock) {
        throw "IntentBlock is required for Invoke-SuperAgent."
    }

    $result = & $IntentBlock @Context

    $nano = Invoke-NanoTx `
        -Agent  $SuperAgent `
        -Action $Intent `
        -Payload ([pscustomobject]$Context) `
        -Result  $result

    return $result
}

# =========================
# SYSTEM HEARTBEAT & ROUTING
# =========================
function Send-SystemHeartbeat {
    [CmdletBinding()]
    param()

    $payload = [pscustomobject]@{
        uptime = (Get-Date)
        node   = "Aegentix-SovereignCore"
    }

    Invoke-NanoTx `
        -Agent  "Aegentix" `
        -Action "heartbeat" `
        -Payload $payload `
        -Result  "ok" | Out-Null
}

function Route-Task {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]    $TaskName,
        [Parameter()][hashtable]          $Payload = @{}
    )

    $agent = "Aegentix"

    $routePayload = [pscustomobject]@{
        task         = $TaskName
        payload      = $Payload
        chosen_agent = $agent
    }

    Invoke-NanoTx `
        -Agent  "Aegentix" `
        -Action "route_task" `
        -Payload $routePayload `
        -Result  $agent | Out-Null

    Invoke-AgentAction `
        -AgentName   $agent `
        -ActionName  $TaskName `
        -Payload     $Payload `
        -ActionBlock { param($payload) return "Task:$TaskName executed by $agent" }
}

# =========================
# CAPTAIN KIRK VOICE INTEGRATION
# =========================
function Invoke-CaptainKirkVoice {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]  $Text,
        [Parameter()][string]           $MemoryId = ([guid]::NewGuid().ToString()),
        [Parameter()][string]           $Persona  = "CaptainKirk"
    )

    $synthesisResult = [pscustomobject]@{
        text    = $Text
        persona = $Persona
        memory  = $MemoryId
        status  = "synthesized"
    }

    $payload = [pscustomobject]@{
        synthesis_text = $Text
        persona        = $Persona
        memory_id      = $MemoryId
    }

    $nano = Invoke-NanoTx `
        -Agent  "CaptainKirk" `
        -Action "voice_synthesis:CaptainKirk" `
        -Payload $payload `
        -Result  $synthesisResult

    return $synthesisResult
}

# =========================
# EXPORTS
# =========================
Export-ModuleMember -Function @(
    "Invoke-NanoTx",
    "Get-NanoStatus",
    "Invoke-AgentAction",
    "Invoke-SuperAgent",
    "Send-SystemHeartbeat",
    "Route-Task",
    "Invoke-CaptainKirkVoice"
)
