# ============================================================
# AEGENTIX REGISTRY - CORE
# ============================================================

$script:Registry = @{
    Agents = @{}
    Capabilities = @{}
    Services = @{}
    Policies = @{}
    State = @{}
}

function Register-Agent {
    param(
        [string]$Name,
        [string]$Type,
        [string]$Path,
        [hashtable]$Capabilities,
        [hashtable]$Metadata = @{}
    )
    
    $agent = @{
        name = $Name
        type = $Type
        path = $Path
        capabilities = $Capabilities
        metadata = $Metadata
        registered = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        status = "active"
    }
    
    $script:Registry.Agents[$Name] = $agent
    $agent | ConvertTo-Json | Out-File "C:\Aegentix\Registry\Agents\$Name.json" -Force
    
    Write-Host "[REGISTRY] Agent registered: $Name" -ForegroundColor Green
    return $agent
}

function Get-RegisteredAgents {
    param([string]$Type)
    $agents = $script:Registry.Agents.Values
    if ($Type) { $agents = $agents | Where-Object { $_.type -eq $Type } }
    return $agents
}

function Register-Capability {
    param(
        [string]$Name,
        [string]$Provider,
        [string]$Version,
        [hashtable]$Config
    )
    
    $capability = @{
        name = $Name
        provider = $Provider
        version = $Version
        config = $Config
        registered = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        status = "active"
    }
    
    $script:Registry.Capabilities[$Name] = $capability
    $capability | ConvertTo-Json | Out-File "C:\Aegentix\Registry\Capabilities\$Name.json" -Force
    
    Write-Host "[REGISTRY] Capability registered: $Name" -ForegroundColor Green
    return $capability
}

function Register-Service {
    param(
        [string]$Name,
        [string]$Type,
        [string]$Endpoint,
        [hashtable]$Config = @{}
    )
    
    $service = @{
        name = $Name
        type = $Type
        endpoint = $Endpoint
        config = $Config
        registered = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        status = "active"
    }
    
    $script:Registry.Services[$Name] = $service
    $service | ConvertTo-Json | Out-File "C:\Aegentix\Registry\Services\$Name.json" -Force
    
    Write-Host "[REGISTRY] Service registered: $Name" -ForegroundColor Green
    return $service
}

function Get-Registry {
    param([string]$Category)
    if ($Category) { return $script:Registry[$Category] }
    return $script:Registry
}

function Save-Registry {
    $script:Registry | ConvertTo-Json -Depth 10 | Out-File "C:\Aegentix\Registry\registry-state.json" -Force
    Write-Host "[REGISTRY] Saved to disk" -ForegroundColor Cyan
}

function Load-Registry {
    if (Test-Path "C:\Aegentix\Registry\registry-state.json") {
        $script:Registry = Get-Content "C:\Aegentix\Registry\registry-state.json" | ConvertFrom-Json
        Write-Host "[REGISTRY] Loaded from disk" -ForegroundColor Cyan
        return $true
    }
    return $false
}

Export-ModuleMember -Function * -ErrorAction SilentlyContinue
