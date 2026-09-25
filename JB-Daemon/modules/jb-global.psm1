function Invoke-JBGlobal {
    param([string]$Action)

    switch ($Action.ToLower()) {

        "refresh-env" {
            return Invoke-JBSovereignRoute -Intent kali.env
        }

        "ping-all" {
            return @{
                Windows = "OK"
                Kali    = Invoke-JBSovereignRoute -Intent kali.ping
            }
        }

        "sysinfo" {
            return Invoke-JBSovereignRoute -Intent kali.exec -Payload "uname -a"
        }

        default {
            return "Unknown Global Action: $Action"
        }
    }
}
