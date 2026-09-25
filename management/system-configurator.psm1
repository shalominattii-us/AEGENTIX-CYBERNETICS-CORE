# Management Plane System Configurator
# Centralized system configuration

param(
    [string]$Action,
    [string]$Component,
    [hashtable]$Settings
)

$configRoot = "C:\Aegentix\management"
$systemConfig = "$configRoot\system-config.json"

# Initialize default config
if (!(Test-Path $systemConfig)) {
    @{
        system = @{
            version = "1.0.0"
            name = "Aegentix Cyberdeck"
            last_updated = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        }
        agents = @{
            coding = @{ enabled = $true; max_workers = 4 }
            infrastructure = @{ enabled = $true; max_workers = 2 }
            research = @{ enabled = $true; max_workers = 2 }
            security = @{ enabled = $true; max_workers = 2 }
            testing = @{ enabled = $true; max_workers = 2 }
        }
        governance = @{
            audit_enabled = $true
            policy_enforced = $true
            compliance_check = $true
        }
        orchestrator = @{
            workflow_enabled = $true
            scheduling_interval = 60
        }
        control = @{
            health_interval = 30
            recovery_enabled = $true
        }
    } | ConvertTo-Json | Set-Content $systemConfig -Force
}

function Get-SystemConfig {
    Get-Content $systemConfig | ConvertFrom-Json
}

function Set-SystemConfig {
    param([string]$Key, [string]$Value)
    
    $config = Get-Content $systemConfig | ConvertFrom-Json
    $config.$Key = $Value
    $config.system.last_updated = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    $config | ConvertTo-Json | Set-Content $systemConfig -Force
    Write-Host "[CONFIG] Updated $Key" -ForegroundColor Green
}

Export-ModuleMember -Function Get-SystemConfig, Set-SystemConfig
