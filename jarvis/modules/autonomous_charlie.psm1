# ============================================================
# AUTONOMOUS CHARLIE - Predictive voice-identity engine
# ============================================================

$Global:AutonomousCharlieActive = $false
$Global:RecentMessageHistory = @()

function Add-CharlieHistory {
    param([string]$Text)
    $entry = [PSCustomObject]@{ Text = $Text; Timestamp = (Get-Date) }
    $Global:RecentMessageHistory += $entry
    if ($Global:RecentMessageHistory.Count -gt 20) {
        $Global:RecentMessageHistory = $Global:RecentMessageHistory[-20..-1]
    }
}

function Get-CharlieTrend {
    if (-not $Global:RecentMessageHistory -or $Global:RecentMessageHistory.Count -eq 0) { return "neutral" }
    $u = ($Global:RecentMessageHistory | Where-Object { $_.Text -match "urgent|now|immediately|critical" }).Count
    $d = ($Global:RecentMessageHistory | Where-Object { $_.Text -match "debate|argue|fight" }).Count
    $f = ($Global:RecentMessageHistory | Where-Object { $_.Text -match "fix|repair|resolve|error" }).Count
    if ($u -ge 3) { return "urgent" }
    if ($d -ge 2) { return "emphatic" }
    if ($f -ge 2) { return "system-failure" }
    return "neutral"
}

function Predict-CharlieVoice {
    param([string]$IncomingText)
    Add-CharlieHistory -Text $IncomingText
    $trend = Get-CharlieTrend
    switch ($trend) {
        "urgent"         { return "./voices/charliekirk_emphatic_processed.vpm" }
        "emphatic"       { return "./voices/charliekirk_emphatic_processed.vpm" }
        "system-failure" { return "./voices/charliekirk_emphatic_processed.vpm" }
        default          { return "./voices/charliekirk_neutral_processed.vpm" }
    }
}

function Invoke-AutonomousCharlie {
    param([string]$Persona,[string]$Message)
    if (-not $Global:AutonomousCharlieActive) { return $Persona }
    if ($Message -match "critical|urgent|now|immediately|fail|broken|stop") {
        return "./voices/charliekirk_emphatic_processed.vpm"
    }
    if ($Message -match "why|explain|how|what|describe|define") {
        return "./voices/charliekirk_slow_processed.vpm"
    }
    $predicted = Predict-CharlieVoice -IncomingText $Message
    if ($predicted -ne "./voices/charliekirk_neutral_processed.vpm") { return $predicted }
    return $Persona
}

function Set-AutonomousCharlie {
    param([bool]$State)
    $Global:AutonomousCharlieActive = $State
    if ($State) { Write-Host "Autonomous Charlie activated - predictive voice identity online." }
    else { Write-Host "Autonomous Charlie deactivated." }
}

Export-ModuleMember -Function Invoke-AutonomousCharlie,Predict-CharlieVoice,Set-AutonomousCharlie,Add-CharlieHistory
