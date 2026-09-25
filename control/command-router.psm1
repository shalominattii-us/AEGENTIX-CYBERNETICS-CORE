# Control Plane Command Router
# Routes commands to appropriate services

param(
    [string]$Command,
    [string]$Target,
    [string[]]$Parameters
)

$routerLog = "C:\Aegentix\control\router\router.log"

function Invoke-Route {
    param([string]$Command, [string]$Target, [string[]]$Parameters)
    
    $route = @{
        command = $Command
        target = $Target
        parameters = $Parameters
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    }
    
    $route | ConvertTo-Json | Out-File -Append -FilePath $routerLog
    
    Write-Host "[ROUTER] Routing: $Command -> $Target" -ForegroundColor Cyan
    
    switch ($Command) {
        "agent" {
            & "C:\Aegentix\orchestrator\task-scheduler.ps1" -Task $Target -Agent $Parameters[0]
        }
        "governance" {
            & "C:\Aegentix\governance\policy-engine.ps1" -Action $Target -Resource $Parameters[0]
        }
        "deploy" {
            & "C:\Aegentix\deploy-scripts\AEGIS7-Deploy.ps1" -Target $Target
        }
        "status" {
            & "C:\Aegentix\control\control-plane.ps1" -Control "state"
        }
        default {
            Write-Host "[ROUTER] Unknown command: $Command" -ForegroundColor Red
        }
    }
}

Export-ModuleMember -Function Invoke-Route
