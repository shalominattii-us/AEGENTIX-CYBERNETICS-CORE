# ============================================================
# JARVISVOICE ENTRYPOINT — Sovereign Voice Identity System
# ============================================================

Import-Module "C:\Aegentix\Jarvis\modules\svie.psm1" -Force
Import-Module "C:\Aegentix\Jarvis\modules\dynamic_charlie.psm1" -Force
Import-Module "C:\Aegentix\Jarvis\modules\voice_firewall.psm1" -Force
Import-Module "C:\Aegentix\Jarvis\modules\autonomous_charlie.psm1" -Force

function Invoke-JarvisVoice {
    param(
        [string]$Message,
        [string]$CurrentModel
    )

    # 1 — Derive SVIE context
    $intent     = Get-VoiceIntent -Text $Message
    $sentiment  = Get-VoiceSentiment -Text $Message
    $pace       = Get-OperatorPace -Text $Message
    $urgency    = Get-UrgencyLevel -Text $Message

    # 2 — Resolve Charlie voice from explicit SVIE outputs
    $persona    = Resolve-CharlieVoice -Intent $intent -Sentiment $sentiment -UrgencyLevel $urgency -OperatorPace $pace

    # 3 — Enforce persona boundaries (Voice Firewall)
    $persona    = Invoke-VoiceFirewall -Persona $persona

    # 4 — Autonomous Charlie predictive override
    $persona    = Invoke-AutonomousCharlie -Persona $persona -Message $Message

    # 5 — Speak using validated model
    $env:PATH += ";C:\Aegentix\Jarvis\bin"
    & jarvis tts --voice $persona --text $Message

    # 6 — Return final model for state tracking
    return $persona
}

Export-ModuleMember -Function Invoke-JarvisVoice
