param(
    [string]$InboundQueuePath      = "C:\Sovereign\queue\inbound",
    [string]$WorkflowFilePath      = "C:\Sovereign\workflows\active.json",
    [string]$LogRootPath           = "C:\Sovereign\logs",
    [string]$LedgerPath            = "C:\Sovereign\ledger\ledger.json",
    [int]$HealthPollSeconds        = 15,
    [int]$LogCompactionMinutes     = 30,
    [int]$MaxRestartAttempts       = 2,
    [int]$RoutingCpuThreshold      = 80,
    [int]$RoutingQueueThreshold    = 100
)

# --- Event Emission ---------------------------------------------------------
function Emit-Event {
    param(
        [string]$Type,
        [hashtable]$Data
    )
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffK"
    $event = [ordered]@{
        timestamp = $timestamp
        type      = $Type
        data      = $Data
    }
    $json = $event | ConvertTo-Json -Depth 6
    $eventLogPath = Join-Path $LogRootPath "events"
    if (-not (Test-Path $eventLogPath)) { New-Item -ItemType Directory -Path $eventLogPath | Out-Null }
    $file = Join-Path $eventLogPath ("event_" + (Get-Random) + ".json")
    $json | Set-Content -Path $file -Encoding UTF8
}

# --- Container Health Sentinel ----------------------------------------------
function Get-ContainerStates {
    $containers = docker ps -a --format "{{.ID}} {{.Names}} {{.Status}}" 2>$null
    $result = @()
    foreach ($line in $containers) {
        $parts = $line -split "\s+", 3
        if ($parts.Count -ge 3) {
            $obj = [pscustomobject]@{
                Id     = $parts[0]
                Name   = $parts[1]
                Status = $parts[2]
            }
            $result += $obj
        }
    }
    return $result
}

function Get-ContainerHealthStatus {
    param([string]$ContainerId)
    $inspect = docker inspect $ContainerId 2>$null | ConvertFrom-Json
    if (-not $inspect) { return $null }
    $state = $inspect[0].State
    $healthStatus = $null
    if ($state.Health) { $healthStatus = $state.Health.Status }
    return [pscustomobject]@{
        Status = $state.Status
        Health = $healthStatus
    }
}

function Enforce-ContainerHealth {
    $containers = Get-ContainerStates
    foreach ($c in $containers) {
        $health = Get-ContainerHealthStatus -ContainerId $c.Id
        if (-not $health) { continue }

        $status = $health.Status
        $healthStatus = $health.Health

        $needsRestart = $false
        if ($status -eq "exited" -or $status -eq "dead") { $needsRestart = $true }
        if ($healthStatus -and $healthStatus -ne "healthy") { $needsRestart = $true }

        if ($needsRestart) {
            Emit-Event -Type "container_failure_detected" -Data @{
                id     = $c.Id
                name   = $c.Name
                status = $status
                health = $healthStatus
            }

            $attempt = 0
            $success = $false
            while ($attempt -lt $MaxRestartAttempts -and -not $success) {
                $attempt++
                try {
                    docker restart $c.Id | Out-Null
                    Start-Sleep -Seconds 3
                    $postHealth = Get-ContainerHealthStatus -ContainerId $c.Id
                    if ($postHealth.Status -eq "running" -and ($postHealth.Health -eq $null -or $postHealth.Health -eq "healthy")) {
                        $success = $true
                        Emit-Event -Type "container_recovered" -Data @{
                            id        = $c.Id
                            name      = $c.Name
                            attempts  = $attempt
                            postState = $postHealth.Status
                            postHealth= $postHealth.Health
                        }
                    }
                } catch {
                    Emit-Event -Type "container_restart_error" -Data @{
                        id      = $c.Id
                        name    = $c.Name
                        attempt = $attempt
                        error   = $_.Exception.Message
                    }
                }
            }

            if (-not $success) {
                Emit-Event -Type "critical_fault" -Data @{
                    id      = $c.Id
                    name    = $c.Name
                    status  = $status
                    health  = $healthStatus
                    attempts= $MaxRestartAttempts
                }
            }
        }
    }
}

# --- Request Routing & Load Management --------------------------------------
function Get-ServiceMetrics {
    return @{
        "mcp-http"   = @{ cpu = 20; queue = 10 }
        "mcp-system" = @{ cpu = 30; queue = 5 }
        "mcp-fs"     = @{ cpu = 15; queue = 2 }
        "runtime"    = @{ cpu = 40; queue = 20 }
        "gaia"       = @{ cpu = 25; queue = 8 }
    }
}

function Route-Request {
    param(
        [hashtable]$Request,
        [hashtable]$Metrics
    )

    $type = $Request.type
    $targetService = switch ($type) {
        "mcp-http"   { "mcp-http" }
        "mcp-system" { "mcp-system" }
        "mcp-fs"     { "mcp-fs" }
        "runtime"    { "runtime" }
        "gaia"       { "gaia" }
        default      { "runtime" }
    }

    $metric = $Metrics[$targetService]
    if ($metric.cpu -ge $RoutingCpuThreshold -or $metric.queue -ge $RoutingQueueThreshold) {
        Emit-Event -Type "load_shift" -Data @{
            originalService = $targetService
            cpu             = $metric.cpu
            queue           = $metric.queue
        }
        $targetService = "$targetService-replica"
    }

    $maxRetries = 3
    $delay = 1
    $success = $false
    $attempt = 0

    while (-not $success -and $attempt -lt $maxRetries) {
        $attempt++
        try {
            $success = $true
        } catch {
            Emit-Event -Type "route_failure" -Data @{
                service = $targetService
                attempt = $attempt
                error   = $_.Exception.Message
            }
            Start-Sleep -Seconds $delay
            $delay = [math]::Min($delay * 2, 30)
        }
    }

    if (-not $success) {
        Emit-Event -Type "route_exhausted" -Data @{
            service = $targetService
            request = $Request
        }
    }
}

function Process-InboundRequests {
    if (-not (Test-Path $InboundQueuePath)) { return }
    $files = Get-ChildItem -Path $InboundQueuePath -Filter "*.json" -File -ErrorAction SilentlyContinue
    if (-not $files) { return }

    $metrics = Get-ServiceMetrics

    foreach ($file in $files) {
        try {
            $json = Get-Content -Path $file.FullName -Raw
            $req = $json | ConvertFrom-Json -Depth 6
            $ht = @{}
            $req.psobject.Properties | ForEach-Object { $ht[$_.Name] = $_.Value }
            Route-Request -Request $ht -Metrics $metrics
            Remove-Item -Path $file.FullName -Force
        } catch {
            Emit-Event -Type "request_parse_error" -Data @{
                file  = $file.FullName
                error = $_.Exception.Message
            }
        }
    }
}

# --- Log Compaction & Ledger Updates ----------------------------------------
function Get-LogFiles {
    if (-not (Test-Path $LogRootPath)) { return @() }
    return Get-ChildItem -Path $LogRootPath -Recurse -File -ErrorAction SilentlyContinue
}

function Compact-Logs {
    $now = Get-Date
    $files = Get-LogFiles
    $summary = @()

    foreach ($file in $files) {
        try {
            $lines = Get-Content -Path $file.FullName -ErrorAction SilentlyContinue
            $errorCount = ($lines | Where-Object { $_ -match "error" }).Count
            $warnCount  = ($lines | Where-Object { $_ -match "warn" }).Count
            $infoCount  = ($lines | Where-Object { $_ -match "info" }).Count

            $summary += [pscustomobject]@{
                path       = $file.FullName
                errorCount = $errorCount
                warnCount  = $warnCount
                infoCount  = $infoCount
                sizeBytes  = $file.Length
                lastWrite  = $file.LastWriteTime
            }

            if ($file.LastWriteTime -lt $now.AddHours(-24)) {
                Remove-Item -Path $file.FullName -Force -ErrorAction SilentlyContinue
            }
        } catch {
            Emit-Event -Type "log_compaction_error" -Data @{
                file  = $file.FullName
                error = $_.Exception.Message
            }
        }
    }

    if (-not (Test-Path (Split-Path $LedgerPath))) {
        New-Item -ItemType Directory -Path (Split-Path $LedgerPath) | Out-Null
    }

    $ledgerEntry = [ordered]@{
        timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffK"
        type      = "log_compaction"
        summary   = $summary
    }

    $existing = @()
    if (Test-Path $LedgerPath) {
        try {
            $existingJson = Get-Content -Path $LedgerPath -Raw
            $existing = $existingJson | ConvertFrom-Json -Depth 6
        } catch { $existing = @() }
    }

    $newLedger = @()
    if ($existing) { $newLedger += $existing }
    $newLedger += $ledgerEntry

    $newLedger | ConvertTo-Json -Depth 8 | Set-Content -Path $LedgerPath -Encoding UTF8

    Emit-Event -Type "ledger_compaction_complete" -Data @{
        entries = $summary.Count
    }
}

# --- Daily Intelligence Report ----------------------------------------------
function Generate-DailyReport {
    $containers = Get-ContainerStates
    $now = Get-Date

    $eventsPath = Join-Path $LogRootPath "events"
    $events = @()
    if (Test-Path $eventsPath) {
        $eventFiles = Get-ChildItem -Path $eventsPath -Filter "*.json" -File -ErrorAction SilentlyContinue
        foreach ($file in $eventFiles) {
            try {
                $json = Get-Content -Path $file.FullName -Raw
                $evt = $json | ConvertFrom-Json -Depth 6
                $events += $evt
            } catch { }
        }
    }

    $autoHealEvents = $events | Where-Object { $_.type -eq "container_recovered" }
    $criticalFaults = $events | Where-Object { $_.type -eq "critical_fault" }
    $routingAnomalies = $events | Where-Object { $_.type -like "route_*" -or $_.type -eq "load_shift" }

    $report = [ordered]@{
        generatedAt      = $now.ToString("yyyy-MM-ddTHH:mm:ss.fffK")
        containerSummary = $containers
        autoHealCount    = $autoHealEvents.Count
        criticalFaults   = $criticalFaults
        routingAnomalies = $routingAnomalies
        suggestions      = @(
            "Review containers with repeated failures.",
            "Inspect services with frequent load_shift events.",
            "Validate workflow definitions for failures."
        )
    }

    $reportPathRoot = Join-Path $LogRootPath "reports"
    if (-not (Test-Path $reportPathRoot)) { New-Item -ItemType Directory -Path $reportPathRoot | Out-Null }
    $reportFile = Join-Path $reportPathRoot ("daily_report_" + $now.ToString("yyyyMMdd") + ".json")
    $report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportFile -Encoding UTF8

    Emit-Event -Type "daily_intel_report" -Data @{
        path = $reportFile
    }
}

# --- Workflow Executor ------------------------------------------------------
function Load-Workflows {
    if (-not (Test-Path $WorkflowFilePath)) { return @() }
    try {
        $json = Get-Content -Path $WorkflowFilePath -Raw
        $wf = $json | ConvertFrom-Json -Depth 8
        if ($wf -is [System.Collections.IEnumerable]) { return $wf }
        return @($wf)
    } catch {
        Emit-Event -Type "workflow_load_error" -Data @{
            path  = $WorkflowFilePath
            error = $_.Exception.Message
        }
        return @()
    }
}

function Execute-WorkflowStep {
    param(
        [string]$WorkflowName,
        [pscustomobject]$Step
    )

    $stepType = $Step.type
    Emit-Event -Type "workflow_step_start" -Data @{
        workflow = $WorkflowName
        step     = $Step
    }

    try {
        switch ($stepType) {
            "shell" {
                $cmd = $Step.command
                if ($cmd) {
                    Invoke-Expression $cmd | Out-Null
                }
            }
            "http" {
                $uri    = $Step.uri
                $method = $Step.method
                $body   = $Step.body
                if (-not $method) { $method = "Post" }
                if ($body) {
                    Invoke-RestMethod -Uri $uri -Method $method -Body ($body | ConvertTo-Json -Depth 6) | Out-Null
                } else {
                    Invoke-RestMethod -Uri $uri -Method $method | Out-Null
                }
            }
            default {
                throw "Unknown step type: $stepType"
            }
        }

        Emit-Event -Type "workflow_step_complete" -Data @{
            workflow = $WorkflowName
            step     = $Step
        }
        return $true
    } catch {
        Emit-Event -Type "workflow_step_failed" -Data @{
            workflow = $WorkflowName
            step     = $Step
            error    = $_.Exception.Message
        }
        return $false
    }
}

function Execute-Workflows {
    $workflows = Load-Workflows
    foreach ($wf in $workflows) {
        $name = $wf.name
        if (-not $name) { $name = "unnamed_" + (Get-Random) }

        Emit-Event -Type "workflow_start" -Data @{
            workflow = $name
        }

        $steps = $wf.steps
        if (-not $steps) {
            Emit-Event -Type "workflow_failed" -Data @{
                workflow = $name
                reason   = "No steps defined"
            }
            continue
        }

        $allSuccess = $true
        foreach ($step in $steps) {
            $attempts = 0
            $maxStepRetries = 3
            $stepSuccess = $false

            while (-not $stepSuccess -and $attempts -lt $maxStepRetries) {
                $attempts++
                $stepSuccess = Execute-WorkflowStep -WorkflowName $name -Step $step
                if (-not $stepSuccess) {
                    Start-Sleep -Seconds 2
                }
            }

            if (-not $stepSuccess) {
                $allSuccess = $false
                break
            }
        }

        if ($allSuccess) {
            Emit-Event -Type "workflow_complete" -Data @{
                workflow = $name
            }
        } else {
            Emit-Event -Type "workflow_failed" -Data @{
                workflow = $name
                reason   = "Step failure"
            }
        }
    }
}

# --- Main Daemon Loop -------------------------------------------------------
$lastHealthPoll      = Get-Date
$lastLogCompaction   = Get-Date
$lastReportDate      = $null

Write-Host "[SOVEREIGN AUTONOMY DAEMON] Starting..." -ForegroundColor Cyan

while ($true) {
    $now = Get-Date

    if (($now - $lastHealthPoll).TotalSeconds -ge $HealthPollSeconds) {
        Enforce-ContainerHealth
        $lastHealthPoll = $now
    }

    Process-InboundRequests

    if (($now - $lastLogCompaction).TotalMinutes -ge $LogCompactionMinutes) {
        Compact-Logs
        $lastLogCompaction = $now
    }

    $localNow = Get-Date
    if ($localNow.Hour -eq 6 -and $localNow.Minute -eq 0) {
        $today = $localNow.Date
        if (-not $lastReportDate -or $lastReportDate -ne $today) {
            Generate-DailyReport
            $lastReportDate = $today
        }
    }

    Execute-Workflows

    Start-Sleep -Milliseconds 500
}
