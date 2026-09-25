# Orchestrator Event Broker
# Handles inter-agent messaging and events

$eventLog = "C:\Aegentix\orchestrator\events\events.log"

function Publish-Event {
    param([string]$EventName, [string]$Source, [string]$Payload)
    
    $event = @{
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        event = $EventName
        source = $Source
        payload = $Payload
    }
    
    $event | ConvertTo-Json | Out-File -Append -FilePath $eventLog
    Write-Host "[EVENT] $EventName from $Source" -ForegroundColor Cyan
    
    # Dispatch to subscribers
    $subscribers = Get-ChildItem "C:\Aegentix\orchestrator\events\subscribers\*.json" -ErrorAction SilentlyContinue
    foreach ($sub in $subscribers) {
        $config = Get-Content $sub.FullName | ConvertFrom-Json
        if ($config.events -contains $EventName) {
            Write-Host "[EVENT] Dispatching to: $($config.name)" -ForegroundColor Yellow
        }
    }
}

function Subscribe-Event {
    param([string]$Name, [string[]]$Events, [string]$Action)
    
    $subscriber = @{
        name = $Name
        events = $Events
        action = $Action
        created = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    }
    
    $subscriber | ConvertTo-Json | Out-File "C:\Aegentix\orchestrator\events\subscribers\$Name.json" -Force
    Write-Host "[EVENT] Subscriber added: $Name" -ForegroundColor Green
}

Export-ModuleMember -Function Publish-Event, Subscribe-Event
