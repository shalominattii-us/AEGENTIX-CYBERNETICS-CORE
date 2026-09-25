function Get-CharlieContext {
    param([string]$Intent,[string]$Sentiment,[int]$UrgencyLevel,[int]$OperatorPace)

    if ($UrgencyLevel -ge 8 -or $Intent -eq "system-failure") { return "urgent" }
    if ($OperatorPace -ge 7) { return "fast" }
    if ($Intent -eq "debate" -or $Sentiment -eq "stressed") { return "emphatic" }
    if ($Intent -eq "explain" -and $OperatorPace -le 4) { return "slow" }
    if ($Sentiment -eq "negative") { return "emotional" }

    return "neutral"
}

function Select-CharlieVoice {
    param([string]$Intent,[string]$Sentiment,[int]$UrgencyLevel,[int]$OperatorPace)

    $context = Get-CharlieContext -Intent $Intent -Sentiment $Sentiment -UrgencyLevel $UrgencyLevel -OperatorPace $OperatorPace

    switch ($context) {
        "urgent"    { return "./voices/charliekirk_emphatic_processed.vpm" }
        "fast"      { return "./voices/charliekirk_fast_processed.vpm" }
        "slow"      { return "./voices/charliekirk_slow_processed.vpm" }
        "emotional" { return "./voices/charliekirk_emotional_processed.vpm" }
        default     { return "./voices/charliekirk_neutral_processed.vpm" }
    }
}

Export-ModuleMember -Function Select-CharlieVoice,Get-CharlieContext
