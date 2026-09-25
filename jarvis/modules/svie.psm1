function Get-VoiceIntent {
    param([string]$Text)
    if ($Text -match "status|report|update") { return "status" }
    if ($Text -match "why|explain|how")      { return "explain" }
    if ($Text -match "alert|warning")        { return "alert" }
    if ($Text -match "fix|repair|resolve")   { return "system-failure" }
    if ($Text -match "debate|argue")         { return "debate" }
    return "conversation"
}

function Get-VoiceSentiment {
    param([string]$Text)
    if ($Text -match "frustrated|angry|upset") { return "negative" }
    if ($Text -match "great|awesome|good")     { return "positive" }
    if ($Text -match "stress|urgent")          { return "stressed" }
    if ($Text -match "think|consider")         { return "reflective" }
    return "neutral"
}

function Get-OperatorPace {
    param([string]$Text)
    $len = $Text.Length
    if ($len -ge 180) { return 3 }
    if ($len -ge 80)  { return 5 }
    if ($len -ge 20)  { return 7 }
    return 9
}

function Get-UrgencyLevel {
    param([string]$Text)
    if ($Text -match "critical|urgent|now|immediately") { return 9 }
    if ($Text -match "soon|asap")                       { return 7 }
    if ($Text -match "status|update")                   { return 5 }
    return 2
}

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

function Resolve-CharlieVoice {
    param(
        [string]$Text,
        [string]$Intent,
        [string]$Sentiment,
        [int]$UrgencyLevel,
        [int]$OperatorPace
    )

    # Explicit SVIE params override auto-derivation
    if ($PSBoundParameters.ContainsKey("Intent")) {
        return Select-CharlieVoice -Intent $Intent -Sentiment $Sentiment -UrgencyLevel $UrgencyLevel -OperatorPace $OperatorPace
    }

    # Auto-derive from text
    $intent    = Get-VoiceIntent -Text $Text
    $sentiment = Get-VoiceSentiment -Text $Text
    $pace      = Get-OperatorPace -Text $Text
    $urgency   = Get-UrgencyLevel -Text $Text

    return Select-CharlieVoice -Intent $intent -Sentiment $sentiment -UrgencyLevel $urgency -OperatorPace $pace
}

Export-ModuleMember -Function Resolve-CharlieVoice,Get-VoiceIntent,Get-VoiceSentiment,Get-OperatorPace,Get-UrgencyLevel,Get-CharlieContext,Select-CharlieVoice
