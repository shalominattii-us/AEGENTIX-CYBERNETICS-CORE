# Background Daemon Loop for Autonomous State Routing
$LogPath = "C:\Aegentix\system_telemetry.log"
Write-Output "🚀 Aegentix Control Plane Daemon Started..."
Write-Output "👁️ Monitoring log channel: $LogPath"

# Establish target evaluation schemas natively
$TaskInstructions = "Categorize the incoming infrastructure state for boundary control."
$TaskCriteria = @{
    "network_fault"  = "connection drops, timeouts, blocked ports, offline mesh keys"
    "database_alert" = "out of memory, connection pool exhaustion, failed queries"
    "general_status" = "standard health checks, informational updates"
}

# Create log file if it does not exist yet
if (-not (Test-Path $LogPath)) { New-Item $LogPath -ItemType File -Force | Out-Null }

# Continuous background evaluation pump
while ($true) {
    # Simulate picking up an active infrastructure delta stream line
    # In full deployment, this tracks your live system event queues
    $RawStream = Get-Content $LogPath -Tail 1 -ErrorAction SilentlyContinue
    
    if ($RawStream -and $RawStream -ne $LastProcessed) {
        $LastProcessed = $RawStream
        Write-Output "📥 Processing Stream Delta: $RawStream"
        
        # Pipeline the string straight into the live Laya classification node
        $Decision = .\Route-Orchestrator.ps1 -StateText $RawStream -Instructions $TaskInstructions -Criteria $TaskCriteria
        
        # Log outcome transaction directly out to an audit history file
        $AuditEntry = [ordered]@{
            Timestamp  = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
            RawInput   = $RawStream
            Outcome    = $Decision.choice
            Confidence = $Decision.confidence
        }
        $AuditEntry | ConvertTo-Json -Compress | Out-File -FilePath "C:\Aegentix\audit_ledger.json" -Append -Encoding utf8
    }
    
    Start-Sleep -Seconds 2
}
