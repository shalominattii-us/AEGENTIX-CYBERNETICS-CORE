function Append-Event {
    param(
        [hashtable]$Event
    )

    $eventDir = "C:\Aegentix\runtime\events"
    if (!(Test-Path $eventDir)) {
        New-Item -Path $eventDir -ItemType Directory | Out-Null
    }

    $id = (Get-Date).ToFileTimeUtc().ToString() + ".jsonl"
    $file = Join-Path $eventDir $id

    $json = $Event | ConvertTo-Json -Depth 20
    Add-Content -LiteralPath $file -Value $json
}

function Apply-Event {
    param(
        [hashtable]$Event
    )

    $statePath = "C:\Aegentix\runtime\state.json"

    if (!(Test-Path $statePath)) {
        throw "State file not found: $statePath"
    }

    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json

    if ($Event.type -eq "update") {
        foreach ($key in $Event.keys) {
            $state.$key = $Event.$key
        }
    }

    $state | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Write-State {
    param(
        [hashtable]$Event
    )

    Append-Event -Event $Event
    Apply-Event -Event $Event
}
