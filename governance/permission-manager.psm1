# Governance Permission Manager
# Manages access control and permissions

$permissionFile = "C:\Aegentix\governance\permissions\permissions.json"

# Initialize default permissions if not exists
if (!(Test-Path $permissionFile)) {
    @{
        default = @{
            agents = @{ read = $true; write = $true; execute = $true }
            governance = @{ read = $true; write = $false; execute = $false }
            orchestrator = @{ read = $true; write = $false; execute = $true }
            control = @{ read = $true; write = $false; execute = $false }
        }
        admins = @{
            agents = @{ read = $true; write = $true; execute = $true }
            governance = @{ read = $true; write = $true; execute = $true }
            orchestrator = @{ read = $true; write = $true; execute = $true }
            control = @{ read = $true; write = $true; execute = $true }
        }
    } | ConvertTo-Json | Set-Content $permissionFile -Force
}

function Get-Permissions {
    param([string]$Role, [string]$Resource)
    
    $perms = Get-Content $permissionFile | ConvertFrom-Json
    $rolePerms = $perms.$Role
    
    if ($Resource) {
        return $rolePerms.$Resource
    }
    return $rolePerms
}

function Set-Permissions {
    param([string]$Role, [string]$Resource, [hashtable]$Permissions)
    
    $perms = Get-Content $permissionFile | ConvertFrom-Json
    $perms.$Role.$Resource = $Permissions
    $perms | ConvertTo-Json | Set-Content $permissionFile -Force
    Write-Host "[PERMISSIONS] Updated $Role -> $Resource" -ForegroundColor Green
}

Export-ModuleMember -Function Get-Permissions, Set-Permissions
