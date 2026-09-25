# Governance Audit Logger
# Tracks all system actions for compliance

param(
    [string]$Action,
    [string]$Resource,
    [string]$User = "system"
)

$auditRoot = "C:\Aegentix\governance\audits"
$auditFile = "$auditRoot\audit-$(Get-Date -Format 'yyyy-MM-dd').json"

function Write-Audit {
    param([string]$Action, [string]$Resource, [string]$User)
    
    $entry = @{
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        user = $User
        action = $Action
        resource = $Resource
        host = $env:COMPUTERNAME
        ip = $env:COMPUTERNAME
    }
    
    $entry | ConvertTo-Json | Out-File -Append -FilePath $auditFile
    Write-Host "[AUDIT] $Action on $Resource by $User" -ForegroundColor Yellow
}

function Get-AuditLog {
    param([string]$Date, [string]$Action, [string]$User)
    
    $files = if ($Date) { @("$auditRoot\audit-$Date.json") } else { Get-ChildItem $auditRoot\*.json }
    
    $results = @()
    foreach ($file in $files) {
        if (Test-Path $file) {
            $results += Get-Content $file | ConvertFrom-Json
        }
    }
    
    if ($Action) { $results = $results | Where-Object { $_.action -eq $Action } }
    if ($User) { $results = $results | Where-Object { $_.user -eq $User } }
    
    return $results
}

Export-ModuleMember -Function Write-Audit, Get-AuditLog
