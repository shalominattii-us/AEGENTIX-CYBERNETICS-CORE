function Invoke-JBSovereignRoute {
    param(
        [Parameter(Mandatory=$true)][string]$Intent,
        [string]$Payload
    )

    switch ($Intent.ToLower()) {

        "kali.exec" {
            if (-not $Payload) { return "ERROR: Missing payload for kali.exec" }
            return Invoke-AegentixKali -Command exec -Args "$Payload"
        }

        "kali.ping" {
            return Invoke-AegentixKali -Command ping
        }

        "kali.health" {
            return Invoke-AegentixKali -Command exec -Args "uptime"
        }

        "kali.env" {
            return Invoke-AegentixKali -Command exec -Args "printenv"
        }

        default {
            return "ERROR: Unknown Sovereign Intent: $Intent"
        }
    }
}
