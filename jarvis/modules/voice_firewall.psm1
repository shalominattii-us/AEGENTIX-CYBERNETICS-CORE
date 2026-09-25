$Global:VoiceIdentities = @{
    "charlie"   = "./voices/charliekirk_neutral_processed.vpm"
    "kirkprime" = "./voices/kirkprime_neutral.vpm"
    "trump"     = "./voices/trump_neutral.vpm"
    "jarvis"    = "./voices/jarvis_default.vpm"
}

$Global:VoiceRules = @{
    "charlie"   = @("charlie")
    "kirkprime" = @("kirkprime")
    "trump"     = @("trump")
    "jarvis"    = @("jarvis")
}

function Get-VoicePersona {
    param([string]$ModelPath)
    foreach ($key in $Global:VoiceIdentities.Keys) {
        if ($ModelPath -like "*$key*") { return $key }
    }
    return "unknown"
}

function Assert-VoiceBoundary {
    param([string]$CurrentModel,[string]$RequestedModel)

    $currentPersona   = Get-VoicePersona -ModelPath $CurrentModel
    $requestedPersona = Get-VoicePersona -ModelPath $RequestedModel

    if ($requestedPersona -eq "unknown") { return $CurrentModel }

    $allowed = $Global:VoiceRules[$currentPersona]

    if ($allowed -contains $requestedPersona) {
        return $RequestedModel
    }

    return $CurrentModel
}

function Enforce-VoiceFirewall {
    param([string]$CurrentModel,[string]$RequestedModel)
    return (Assert-VoiceBoundary -CurrentModel $CurrentModel -RequestedModel $RequestedModel)
}

function Invoke-VoiceFirewall {
    param([string]$Persona)

    # Validate persona against registry
    $personaKey = Get-VoicePersona -ModelPath $Persona
    if ($personaKey -ne "unknown") {
        return $Persona
    }
    # Unknown persona — return neutral default
    return "./voices/charliekirk_neutral_processed.vpm"
}

Export-ModuleMember -Function Enforce-VoiceFirewall,Invoke-VoiceFirewall
