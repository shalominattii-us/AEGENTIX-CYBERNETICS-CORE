[CmdletBinding()]
param(
  [string]$OutputPath = "platform/service-registry/observations/docker-runtime.json",
  [switch]$IncludeStopped
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-DockerJson {
  param([string[]]$Arguments)

  $raw = & docker @Arguments 2>&1
  if ($LASTEXITCODE -ne 0) {
    throw "Docker command failed: docker $($Arguments -join ' ')`n$raw"
  }

  return $raw
}

function Get-HealthState {
  param(
    [string]$State,
    [AllowNull()][string]$HealthStatus
  )

  if ($State -ne "running") { return "stopped" }
  switch ($HealthStatus) {
    "healthy"   { return "healthy" }
    "unhealthy" { return "unhealthy" }
    "starting"  { return "starting" }
    default     { return "unknown" }
  }
}

$null = Invoke-DockerJson -Arguments @("version", "--format", "{{json .Server}}")
$engine = (Invoke-DockerJson -Arguments @("version", "--format", "{{.Server.Version}}") | Select-Object -First 1).Trim()

$psArgs = @("ps", "--no-trunc", "--format", "{{.ID}}")
if ($IncludeStopped) { $psArgs = @("ps", "-a", "--no-trunc", "--format", "{{.ID}}") }

$containerIds = @(Invoke-DockerJson -Arguments $psArgs | Where-Object { $_ -and $_.Trim() })
$services = [System.Collections.Generic.List[object]]::new()

foreach ($containerId in $containerIds) {
  $inspectRaw = Invoke-DockerJson -Arguments @("inspect", $containerId)
  $inspect = ($inspectRaw -join "`n" | ConvertFrom-Json)[0]

  $ports = [System.Collections.Generic.List[object]]::new()
  if ($inspect.NetworkSettings.Ports) {
    foreach ($property in $inspect.NetworkSettings.Ports.PSObject.Properties) {
      $parts = $property.Name -split "/"
      $privatePort = [int]$parts[0]
      $protocol = if ($parts.Count -gt 1) { $parts[1] } else { "tcp" }
      $bindings = @($property.Value)

      if ($bindings.Count -eq 0 -or $null -eq $bindings[0]) {
        $ports.Add([ordered]@{
          privatePort = $privatePort
          publicPort  = $null
          publicIp    = $null
          protocol    = $protocol
        })
      }
      else {
        foreach ($binding in $bindings) {
          $ports.Add([ordered]@{
            privatePort = $privatePort
            publicPort  = if ($binding.HostPort) { [int]$binding.HostPort } else { $null }
            publicIp    = if ($binding.HostIp) { [string]$binding.HostIp } else { $null }
            protocol    = $protocol
          })
        }
      }
    }
  }

  $labels = [ordered]@{}
  if ($inspect.Config.Labels) {
    foreach ($label in $inspect.Config.Labels.PSObject.Properties) {
      $labels[$label.Name] = [string]$label.Value
    }
  }

  $networks = @()
  if ($inspect.NetworkSettings.Networks) {
    $networks = @($inspect.NetworkSettings.Networks.PSObject.Properties.Name | Sort-Object)
  }

  $healthStatus = $null
  if ($inspect.State.Health) { $healthStatus = [string]$inspect.State.Health.Status }

  $imageDigest = $null
  try {
    $repoDigests = @($inspect.RepoDigests)
    if ($repoDigests.Count -gt 0) { $imageDigest = [string]$repoDigests[0] }
  }
  catch { }

  $services.Add([ordered]@{
    runtimeId   = [string]$inspect.Id
    name        = ([string]$inspect.Name).TrimStart("/")
    runtime     = "docker"
    state       = [string]$inspect.State.Status
    health      = Get-HealthState -State ([string]$inspect.State.Status) -HealthStatus $healthStatus
    image       = [string]$inspect.Config.Image
    imageDigest = $imageDigest
    createdAt   = if ($inspect.Created) { ([datetime]$inspect.Created).ToUniversalTime().ToString("o") } else { $null }
    startedAt   = if ($inspect.State.StartedAt -and $inspect.State.StartedAt -notmatch "^0001-") { ([datetime]$inspect.State.StartedAt).ToUniversalTime().ToString("o") } else { $null }
    ports       = @($ports)
    labels      = $labels
    networks    = $networks
    restartCount = if ($null -ne $inspect.RestartCount) { [int]$inspect.RestartCount } else { $null }
    exitCode    = if ($null -ne $inspect.State.ExitCode) { [int]$inspect.State.ExitCode } else { $null }
    error       = if ($inspect.State.Error) { [string]$inspect.State.Error } else { $null }
  })
}

$observation = [ordered]@{
  schemaVersion = "1.0.0"
  observationId = "docker-$([guid]::NewGuid().ToString('n'))"
  source        = "docker"
  observedAt    = (Get-Date).ToUniversalTime().ToString("o")
  host          = [ordered]@{
    hostname      = [System.Net.Dns]::GetHostName()
    platform      = [System.Environment]::OSVersion.Platform.ToString()
    osVersion     = [System.Environment]::OSVersion.VersionString
    engineVersion = $engine
  }
  services      = @($services | Sort-Object name)
}

$resolved = [System.IO.Path]::GetFullPath($OutputPath)
$directory = Split-Path -Parent $resolved
if (-not (Test-Path $directory)) {
  New-Item -ItemType Directory -Path $directory -Force | Out-Null
}

$observation | ConvertTo-Json -Depth 20 | Set-Content -Path $resolved -Encoding utf8NoBOM

$running = @($services | Where-Object state -eq "running").Count
$unhealthy = @($services | Where-Object health -eq "unhealthy").Count
Write-Host "AEGENTIX Docker observation written to $resolved"
Write-Host "Containers: $($services.Count) | Running: $running | Unhealthy: $unhealthy"
