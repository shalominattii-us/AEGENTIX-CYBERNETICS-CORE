# ============================================================
# AEGIS SOVEREIGN CONFIG — Central configuration for the
# sovereign nanotransaction runtime
# ============================================================

$Global:AegisSovereignConfig = @{
    # EOC staking defaults
    DefaultStakeRatio    = 0.15
    DefaultRewardToken   = "EOC"
    DefaultNetwork       = "mainnet"
    DefaultIntegrityScore = 0.99
    DefaultRewardAmount   = 1.0

    # API
    EOCApiUrl            = "http://localhost:5001/api/eoc/stake"
    APITimeoutSeconds     = 10

    # Ledger
    NanoLedgerPath        = Join-Path $PSScriptRoot "system_nano_ledger.jsonl"
    MaxLedgerEntries      = 10000

    # Agent identity
    SystemAgent           = "Aegentix"
    SystemComponent       = "sovereign-mcp"

    # Reward multipliers
    VoiceRewardPerKB      = 0.1
    VoiceRewardMinimum    = 0.5
    HeartbeatReward       = 0.05
    MemoryWriteReward     = 0.3
    PersonaSwitchReward   = 0.25
    DelegationReward      = 0.5
    RouteTaskReward       = 0.2
    AgentActionDefault    = 0.5
    SuperAgentDefault     = 1.0

    # Super-agent rewards by intent
    SuperAgentRewards = @{
        "status"         = 1.0
        "explain"        = 1.5
        "system-failure" = 3.0
        "alert"          = 2.0
        "delegation"     = 2.0
        "planning"       = 2.5
    }

    # Agent action rewards by action type
    ActionRewards = @{
        "voice-synthesis"   = 1.0
        "intent-derivation" = 0.3
        "persona-check"     = 0.3
        "memory-write"      = 0.3
        "route_task"        = 0.2
    }

    # Module paths
    ModulesPath = $PSScriptRoot

    # Voice stack
    VoiceModules = @(
        "svie.psm1"
        "dynamic_charlie.psm1"
        "voice_firewall.psm1"
        "autonomous_charlie.psm1"
        "jarvis_voice.psm1"
    )

    # Nanotx emitter
    NanotxModule = "nanotx_emitter.psm1"
}

# ============================================================
# Accessor helpers
# ============================================================

function Get-SovereignConfig {
    return $Global:AegisSovereignConfig
}

function Get-ConfigPath {
    param([string]$Key)
    if ($Global:AegisSovereignConfig.ContainsKey($Key)) {
        return $Global:AegisSovereignConfig[$Key]
    }
    return $null
}

function Set-SovereignConfig {
    param(
        [string]$Key,
        [object]$Value
    )
    $Global:AegisSovereignConfig[$Key] = $Value
}

# ============================================================
# NanoTxConfig — nanotx-specific sub-config
# ============================================================

$Global:AegisSovereignConfig.NanoTxConfig = @{
    DefaultStakeRatio      = 0.15
    DefaultIntegrityScore  = 0.99
    DefaultRewardAmount    = 1.0
    DefaultRewardToken     = "EOC"
    DefaultNetwork         = "mainnet"
    APITimeoutSeconds       = 10
    LedgerPath             = $Global:AegisSovereignConfig.NanoLedgerPath
    MaxLedgerEntries       = 10000
}

# ============================================================
# Export
# ============================================================

Export-ModuleMember `
    -Function @(
        "Get-SovereignConfig",
        "Get-ConfigPath",
        "Set-SovereignConfig"
    )
