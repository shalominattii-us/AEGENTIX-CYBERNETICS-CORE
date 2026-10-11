<#
  Hermes / JARVIS — unit bootstrap (Windows, ROG Ally X class hardware)

  Fully local, no hosted services. Run from the repo root:

      powershell -ExecutionPolicy Bypass -File .\install\bootstrap-unit.ps1

  What it does, in order:
    1. verifies Bun (installs it if missing, via the official local installer)
    2. installs workspace dependencies
    3. probes the local inference surfaces: Ollama :11434 and LM Studio :1234
    4. pulls a small fallback model into Ollama if nothing is resident
    5. writes/patches .env (governor endpoint + jarvis endpoints)
    6. pushes the SQLite/Turso schema
    7. starts the console on the port fixed in .runable\ports.json
#>

param(
  [string]$GovernorUrl = "http://localhost:9119",
  [string]$FallbackModel = "qwen2.5:7b-instruct",
  [switch]$SkipModelPull
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Say($msg, $tone = "Gray") { Write-Host "  $msg" -ForegroundColor $tone }
function Head($msg) { Write-Host "`n[$msg]" -ForegroundColor Cyan }

function Test-Endpoint([string]$url) {
  try {
    $null = Invoke-RestMethod -Uri $url -TimeoutSec 2 -Method Get
    return $true
  } catch { return $false }
}

Head "1/7 runtime"
if (-not (Get-Command bun -ErrorAction SilentlyContinue)) {
  Say "bun not found — installing locally" "Yellow"
  irm bun.sh/install.ps1 | iex
  $env:Path = "$env:USERPROFILE\.bun\bin;$env:Path"
}
Say "bun $(bun --version)" "Green"

Head "2/7 dependencies"
bun install
if ($LASTEXITCODE -ne 0) { throw "bun install failed" }
Say "workspace installed" "Green"

Head "3/7 local inference"
$ollamaUp = Test-Endpoint "http://localhost:11434/api/tags"
$lmStudioUp = Test-Endpoint "http://localhost:1234/v1/models"
Say ("ollama   :11434  " + $(if ($ollamaUp) { "UP" } else { "DOWN" })) $(if ($ollamaUp) { "Green" } else { "Yellow" })
Say ("lmstudio :1234   " + $(if ($lmStudioUp) { "UP" } else { "DOWN" })) $(if ($lmStudioUp) { "Green" } else { "Yellow" })

if (-not $ollamaUp -and (Get-Command ollama -ErrorAction SilentlyContinue)) {
  Say "starting ollama serve in the background" "Yellow"
  Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
  Start-Sleep -Seconds 4
  $ollamaUp = Test-Endpoint "http://localhost:11434/api/tags"
}
if (-not $ollamaUp -and -not $lmStudioUp) {
  Say "no local model server reachable — Jarvis will run in retrieval-only mode" "Yellow"
  Say "install Ollama (https://ollama.com/download) or load a model in LM Studio, then re-run" "Yellow"
}

Head "4/7 model"
if ($ollamaUp -and -not $SkipModelPull) {
  $tags = (Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5).models
  if (-not $tags -or $tags.Count -eq 0) {
    Say "no model resident — pulling $FallbackModel (this is the only network fetch)" "Yellow"
    ollama pull $FallbackModel
  } else {
    Say ("resident: " + (($tags | ForEach-Object { $_.name }) -join ", ")) "Green"
  }
} else {
  Say "skipped" "Gray"
}

Head "5/7 environment"
$envPath = Join-Path $root ".env"
if (-not (Test-Path $envPath)) { New-Item -ItemType File -Path $envPath | Out-Null }
$lines = @(Get-Content $envPath -ErrorAction SilentlyContinue)

function Set-EnvLine([string]$key, [string]$value) {
  $script:lines = @($script:lines | Where-Object { $_ -notmatch "^\s*$key=" })
  $script:lines += "$key=$value"
}

Set-EnvLine "HERMES_GOVERNOR_URL" $GovernorUrl
Set-EnvLine "JARVIS_ENDPOINTS" "http://localhost:1234/v1,http://localhost:11434/v1"
Set-Content -Path $envPath -Value $lines
Say "HERMES_GOVERNOR_URL=$GovernorUrl" "Green"
Say "JARVIS_ENDPOINTS=http://localhost:1234/v1,http://localhost:11434/v1" "Green"

Head "6/7 schema"
Push-Location (Join-Path $root "packages\web")
bun run db:push
$pushCode = $LASTEXITCODE
Pop-Location
if ($pushCode -ne 0) {
  Say "db:push failed — check TURSO_* / DATABASE_URL in .env" "Yellow"
} else {
  Say "schema applied; control plane and galaxy seed on first request" "Green"
}

Head "7/7 console"
$portsFile = Join-Path $root ".runable\ports.json"
$port = "4200"
if (Test-Path $portsFile) {
  $ports = Get-Content $portsFile -Raw | ConvertFrom-Json
  if ($ports.website) { $port = $ports.website }
}
Say "starting on http://localhost:$port" "Green"
Say "governor console  http://localhost:$port/governor" "Gray"
Say "galaxy            http://localhost:$port/galaxy" "Gray"
Say "notebook          http://localhost:$port/notebook" "Gray"
Say "jarvis            http://localhost:$port/jarvis" "Gray"
bun run dev
