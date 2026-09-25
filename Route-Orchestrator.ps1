param (
    [Parameter(Mandatory = $true)]
    $StateText,
    
    [Parameter(Mandatory = $true)]
    $Instructions,
    
    [Parameter(Mandatory = $true)]
    [hashtable]$Criteria
)

# Pull the decision payload directly from your local Laya server engine
$Result = Invoke-SystemOne -StateText $StateText -Instructions $Instructions -Criteria $Criteria

# Process the operational pipeline based on the deterministic choice
if ($Result.choice -eq "agent_execute") {
    Write-Output "🟢 Verification Pass: Dispatching Sovereign Swarm token to the execution pipeline..."
} elseif ($Result.choice -eq "agent_fallback") {
    Write-Warning "⚠️ Operational Fallback: Intercepted system exception profile. Halting execution loop."
}
