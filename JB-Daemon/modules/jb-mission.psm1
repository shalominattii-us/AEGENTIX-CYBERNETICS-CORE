function Invoke-JBMission {
    param(
        [Parameter(Mandatory=$true)][string]$MissionName,
        [string]$Payload
    )

    switch ($MissionName.ToLower()) {

        "scan-net" {
            return Invoke-JBSovereignRoute -Intent kali.exec -Payload "ip a"
        }

        "scan-dns" {
            return Invoke-JBSovereignRoute -Intent kali.exec -Payload "dig google.com"
        }

        "sys-check" {
            return Invoke-JBSovereignRoute -Intent kali.exec -Payload "uptime"
        }

        "custom" {
            if (-not $Payload) { return "ERROR: custom mission requires payload" }
            return Invoke-JBSovereignRoute -Intent kali.exec -Payload "$Payload"
        }

        default {
            return "Unknown Mission: $MissionName"
        }
    }
}
