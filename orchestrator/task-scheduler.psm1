# Orchestrator Task Scheduler
# Schedules and coordinates agent tasks

param(
    [string]$Schedule,
    [string]$Task,
    [string]$Agent
)

$scheduleRoot = "C:\Aegentix\orchestrator\schedules"

function New-ScheduledTask {
    param([string]$Name, [string]$Frequency, [string]$Task, [string]$Agent)
    
    $task = @{
        name = $Name
        frequency = $Frequency
        task = $Task
        agent = $Agent
        created = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        status = "scheduled"
    }
    
    $task | ConvertTo-Json | Out-File -Append -FilePath "$scheduleRoot\$Name.json"
    Write-Host "[SCHEDULER] Task scheduled: $Name ($Frequency)" -ForegroundColor Green
}

function Get-ScheduledTasks {
    Get-ChildItem $scheduleRoot\*.json | ForEach-Object {
        Get-Content $_.FullName | ConvertFrom-Json
    }
}

Export-ModuleMember -Function New-ScheduledTask, Get-ScheduledTasks
