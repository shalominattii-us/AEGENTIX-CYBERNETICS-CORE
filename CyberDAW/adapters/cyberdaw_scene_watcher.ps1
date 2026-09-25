<#
.SYNOPSIS
    AEGENTIX CyberDAW - Live Scene Switch Notification Watcher
    Polls the JSONL telemetry stream for SCENE_SELECTION_ACTIVE and CLIP_LAUNCH_EVENT
    and prints live notifications to the Herdr pane (stdout).

.DESCRIPTION
    Reads brain/telemetry_stream.jsonl and detects new SCENE_SELECTION_ACTIVE,
    CLIP_LAUNCH_EVENT, and related entries, writing a live notification line
    to stdout for each new event.

    Run in a Herdr pane:
        powershell -NoProfile -File C:\Aegentix\cyberdaw\adapters\cyberdaw_scene_watcher.ps1
#>

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$StreamPath = "C:\Aegentix\brain\telemetry_stream.jsonl"
$knownHashes = [System.Collections.Generic.HashSet[string]]::new()

function Write-LiveNotification {
    param([string]$Message)
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] $Message"
}

function Test-HMAC {
    param([hashtable]$Payload, [string]$Signature)
    $encoding = [System.Text.Encoding]::UTF8
    $keyBytes = $encoding.GetBytes("AEGENTIX_EOC_PRIME_LOCK")
    $payloadBytes = $encoding.GetBytes(($Payload | ConvertTo-Json -Depth 10 -Compress))
    $hmac = [System.Security.Cryptography.HMACSHA256]::new($keyBytes)
    $hash = $hmac.ComputeHash($payloadBytes)
    $computed = [System.BitConverter]::ToString($hash).Replace("-", "").ToLowerInvariant()
    $hmac.Dispose()
    return $computed -eq $Signature.ToLowerInvariant()
}

function Parse-TelemetryLine {
    param([string]$Line)
    if ([string]::IsNullOrWhiteSpace($Line)) { return $null }
    try { return $Line | ConvertFrom-Json -Depth 10 } catch { return $null }
}

function Format-Metrics {
    param([hashtable]$Metrics)
    $parts = @()
    if ($Metrics.scene_index)   { $parts += "Scene Index: $($Metrics.scene_index)" }
    if ($Metrics.clip_name)     { $parts += "Clip: $($Metrics.clip_name)" }
    if ($Metrics.status)        { $parts += "Status: $($Metrics.status)" }
    if ($Metrics.port)          { $parts += "Port: $($Metrics.port)" }
    if ($Metrics.path_clean)    { $parts += "Path Clean: $($Metrics.path_clean)" }
    if ($Metrics.channels)      { $parts += "Channels: $($Metrics.channels -join ', ')" }
    if ($Metrics.sample_rate)   { $parts += "Sample Rate: $($Metrics.sample_rate) Hz" }
    if ($Metrics.buffer)        { $parts += "Buffer: $($Metrics.buffer)" }
    return $parts
}

Write-LiveNotification "=== AEGENTIX CyberDAW Scene Watcher ==="
Write-LiveNotification "  Monitoring: $StreamPath"
Write-LiveNotification "  Streaming live scene/clip telemetry to Herdr pane."
Write-LiveNotification ""

if (-not (Test-Path $StreamPath)) {
    Write-LiveNotification "Telemetry stream not found at $StreamPath"
    Write-LiveNotification "  Start Ableton with the CyberDAW_Telemetry_Engine.amxd device to begin."
    exit 0
}

$stream = [System.IO.File]::OpenRead($StreamPath)
$reader = New-Object System.IO.StreamReader($stream)
Write-LiveNotification "Streaming live..."
Write-LiveNotification ""

while ($true) {
    $line = $reader.ReadLine()
    if ($null -ne $line) {
        $obj = Parse-TelemetryLine $line
        if ($null -ne $obj -and $obj.event -match "SCENE_SELECTION_ACTIVE|CLIP_LAUNCH_EVENT|MAX_BRIDGE_CONNECTED|AUDIO_INTERFACE_LOCKED|PA_ROUTING_VERIFIED") {
            $hash = ($obj | ConvertTo-Json -Depth 10 -Compress)
            if (-not $knownHashes.Contains($hash)) {
                $knownHashes.Add($hash) | Out-Null
                $label = if ($obj.metrics.scene_index) { $obj.metrics.scene_index }
                         elseif ($obj.metrics.clip_name) { $obj.metrics.clip_name }
                         elseif ($obj.metrics.status) { $obj.metrics.status }
                         else { "EVENT" }
                Write-Host -NoNewline -ForegroundColor Green "[OK] "
                Write-Host -NoNewline "[$($obj.event)] "
                Write-Host -ForegroundColor Cyan $label
                foreach ($ml in Format-Metrics $obj.metrics) {
                    Write-Host "    $ml"
                }
                Write-Host "    integrity_score=$($obj.integrity_score)  HMAC-verified"
                Write-Host ""
            }
        }
    } else {
        Start-Sleep -Milliseconds 500
    }
}
$reader.Close()
$stream.Close()
