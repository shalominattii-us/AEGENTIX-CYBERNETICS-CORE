# ============================================================
# AEGENTIX CONTROL - OPERATIONAL PLANE
# ============================================================

function Control-GetState {
    param([string]$Key)
    
    $stateFile = "C:\Aegentix\Control\Operational\state.json"
    if (Test-Path $stateFile) {
        $state = Get-Content $stateFile | ConvertFrom-Json
        if ($Key) { return $state.$Key }
        return $state
    }
    return @{}
}

function Control-SetState {
    param(
        [string]$Key,
        $Value
    )
    
    $stateFile = "C:\Aegentix\Control\Operational\state.json"
    $state = if (Test-Path $stateFile) { Get-Content $stateFile | ConvertFrom-Json } else { @{} }
    $state.$Key = $Value
    $state.lastUpdated = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
    $state | ConvertTo-Json | Set-Content $stateFile
    Write-Host "[CONTROL] State updated: $Key" -ForegroundColor Green
}

function Control-GetMetrics {
    $metrics = @{
        timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        host = $env:COMPUTERNAME
        processes = @{
            powershell = (Get-Process powershell -ErrorAction SilentlyContinue).Count
            node = (Get-Process node -ErrorAction SilentlyContinue).Count
        }
        resources = @{
            memory = [math]::Round((Get-Counter "\Memory\Available MBytes").CounterSamples.CookedValue, 0)
            cpu = [math]::Round((Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples.CookedValue, 0)
            disk = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
        }
        agents = (Get-ChildItem C:\Aegentix\agents\ -Directory -ErrorAction SilentlyContinue).Count
        uptime = (Get-Date) - (Get-Process -Id $PID).StartTime
    }
    return $metrics
}

function Control-ExecuteTactical {
    param(
        [string]$Operation,
        [hashtable]$Parameters = @{}
    )
    
    Write-Host "[CONTROL] Tactical operation: $Operation" -ForegroundColor Magenta
    
    switch ($Operation) {
        "deploy" {
            Write-Host "[CONTROL] Deploying: $($Parameters.Target)" -ForegroundColor Yellow
            & "C:\Aegentix\deploy-scripts\AEGIS7-Deploy.ps1" -Target $Parameters.Target 2>$null
        }
        "validate" {
            Write-Host "[CONTROL] Validating: $($Parameters.Resource)" -ForegroundColor Yellow
            & "C:\Aegentix\governance\policy-engine.ps1" -Action "validate" -Resource $Parameters.Resource 2>$null
        }
        "audit" {
            Write-Host "[CONTROL] Auditing: $($Parameters.Resource)" -ForegroundColor Yellow
            & "C:\Aegentix\governance\audit-logger.ps1" -Action "audit" -Resource $Parameters.Resource 2>$null
        }
        "restart" {
            Write-Host "[CONTROL] Restarting: $($Parameters.Service)" -ForegroundColor Yellow
            Get-Process | Where-Object { $_.ProcessName -match $Parameters.Service } | Stop-Process -Force 2>$null
            Start-Sleep -Seconds 2
            Start-Job -Name $Parameters.Service -ScriptBlock { & $args[0] } -ArgumentList $Parameters.Path 2>$null
        }
        default {
            Write-Host "[CONTROL] Unknown operation: $Operation" -ForegroundColor Red
        }
    }
}

function Control-ExecuteStrategic {
    param(
        [string]$Directive,
        [hashtable]$Parameters = @{}
    )
    
    Write-Host "[CONTROL] Strategic directive: $Directive" -ForegroundColor Cyan
    
    switch ($Directive) {
        "orchestrate" {
            Write-Host "[CONTROL] Orchestrating: $($Parameters.Workflow)" -ForegroundColor Yellow
            & "C:\Aegentix\orchestrator\workflow-engine.ps1" -Workflow $Parameters.Workflow 2>$null
        }
        "govern" {
            Write-Host "[CONTROL] Governing: $($Parameters.Policy)" -ForegroundColor Yellow
            & "C:\Aegentix\governance\policy-engine.ps1" -Policy $Parameters.Policy 2>$null
        }
        "schedule" {
            Write-Host "[CONTROL] Scheduling: $($Parameters.Task)" -ForegroundColor Yellow
            & "C:\Aegentix\orchestrator\task-scheduler.ps1" -Task $Parameters.Task 2>$null
        }
        default {
            Write-Host "[CONTROL] Unknown directive: $Directive" -ForegroundColor Red
        }
    }
}

Export-ModuleMember -Function * -ErrorAction SilentlyContinue
