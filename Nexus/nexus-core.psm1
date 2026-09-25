# ============================================================
# AEGENTIX NEXUS - COMMAND & EVENT BUS
# ============================================================

$script:Nexus = @{
    Commands = @{}
    Events = @{}
    Queries = @{}
    Handlers = @{}
    Subscribers = @{}
}

function Nexus-RegisterCommand {
    param(
        [string]$Name,
        [scriptblock]$Handler,
        [hashtable]$Schema = @{}
    )
    
    $command = @{
        name = $Name
        handler = $Handler
        schema = $Schema
        registered = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    }
    
    $script:Nexus.Commands[$Name] = $command
    Write-Host "[NEXUS] Command registered: $Name" -ForegroundColor Green
}

function Nexus-ExecuteCommand {
    param(
        [string]$Name,
        [hashtable]$Parameters = @{}
    )
    
    if ($script:Nexus.Commands.ContainsKey($Name)) {
        $command = $script:Nexus.Commands[$Name]
        Write-Host "[NEXUS] Executing command: $Name" -ForegroundColor Cyan
        $result = & $command.handler $Parameters
        return $result
    } else {
        Write-Host "[NEXUS] Command not found: $Name" -ForegroundColor Red
        return $null
    }
}

function Nexus-RegisterEventHandler {
    param(
        [string]$EventName,
        [scriptblock]$Handler
    )
    
    if (!$script:Nexus.Handlers.ContainsKey($EventName)) {
        $script:Nexus.Handlers[$EventName] = @()
    }
    $script:Nexus.Handlers[$EventName] += $Handler
    Write-Host "[NEXUS] Event handler registered: $EventName" -ForegroundColor Green
}

function Nexus-EmitEvent {
    param(
        [string]$EventName,
        [hashtable]$Data = @{}
    )
    
    $event = @{
        name = $EventName
        data = $Data
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        source = $env:COMPUTERNAME
    }
    
    Write-Host "[NEXUS] Event emitted: $EventName" -ForegroundColor Cyan
    $event | ConvertTo-Json | Out-File "C:\Aegentix\Nexus\Events\$EventName-$(Get-Date -Format 'yyyyMMddHHmmss').json" -Force
    
    if ($script:Nexus.Handlers.ContainsKey($EventName)) {
        foreach ($handler in $script:Nexus.Handlers[$EventName]) {
            try { & $handler $event } catch { Write-Host "[NEXUS] Handler error: $_" -ForegroundColor Red }
        }
    }
}

function Nexus-RegisterQuery {
    param(
        [string]$Name,
        [scriptblock]$Handler,
        [hashtable]$Schema = @{}
    )
    
    $query = @{
        name = $Name
        handler = $Handler
        schema = $Schema
        registered = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    }
    
    $script:Nexus.Queries[$Name] = $query
    Write-Host "[NEXUS] Query registered: $Name" -ForegroundColor Green
}

function Nexus-ExecuteQuery {
    param(
        [string]$Name,
        [hashtable]$Parameters = @{}
    )
    
    if ($script:Nexus.Queries.ContainsKey($Name)) {
        $query = $script:Nexus.Queries[$Name]
        Write-Host "[NEXUS] Executing query: $Name" -ForegroundColor Cyan
        return & $query.handler $Parameters
    } else {
        Write-Host "[NEXUS] Query not found: $Name" -ForegroundColor Red
        return $null
    }
}

Export-ModuleMember -Function * -ErrorAction SilentlyContinue
