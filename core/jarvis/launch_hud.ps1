param(
  [switch]$DryRun,
  [switch]$NoWindow
)
$ErrorActionPreference = 'Stop'
$core = 'C:\AEGENTIX-CYBERNETICS-CORE'
$env:PYTHONPATH = $core
$py = Join-Path $core '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
$code = @'
import json
from core.jarvis.resolve_hud import resolve_hud
print(json.dumps(resolve_hud(), indent=2))
'@
Push-Location -LiteralPath $core
try {
  $resolvedJson = & $py -c $code
  if ($LASTEXITCODE -ne 0) { throw "HUD resolve failed: $resolvedJson" }
  $r = $resolvedJson | ConvertFrom-Json
  if (-not $r.ok) { throw ("HUD resolve not ok: " + ($r.errors -join '; ')) }
  if (-not $env:AEGENTIX_MCP_BASE_URL) { $env:AEGENTIX_MCP_BASE_URL = $r.mcp_base_url }
  if (-not $env:AEGENTIX_GATEWAY_URL) { $env:AEGENTIX_GATEWAY_URL = $r.gateway_base_url }
  if (-not $env:AEGENTIX_MCP_TOKEN -and -not $env:AEGENTIX_API_TOKEN -and -not $env:AEGENTIX_ALLOW_LOCAL_NOAUTH) { $env:AEGENTIX_ALLOW_LOCAL_NOAUTH = '1' }
  $logDir = Join-Path $core 'data\logs'; New-Item -ItemType Directory -Force -Path $logDir | Out-Null
  $outLog = Join-Path $logDir 'hud_launch.out.log'; $errLog = Join-Path $logDir 'hud_launch.err.log'
  Write-Host "HUD root: $($r.hud_root)"
  Write-Host "Python: $($r.python)"
  Write-Host "Entry: $($r.entrypoint)"
  Write-Host "MCP: $env:AEGENTIX_MCP_BASE_URL"
  Write-Host "Gateway: $env:AEGENTIX_GATEWAY_URL"
  if ($DryRun) { Write-Host 'DryRun: not launching.'; exit 0 }
  $argList = @($r.entrypoint)
  if ($r.args) { $argList += @($r.args) }
  $proc = Start-Process -FilePath $r.python -ArgumentList $argList -WorkingDirectory $r.cwd -PassThru -RedirectStandardOutput $outLog -RedirectStandardError $errLog
  Start-Sleep -Milliseconds 1500
  $p = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
  if ($null -eq $p) {
    Write-Warning "HUD process exited early. See: $errLog"
    if (Test-Path $errLog) { Get-Content $errLog -Tail 60 }
    exit 1
  }
  Write-Host "Launched JARVIS Holographic HUD (PID $($p.Id)) via core resolver. Logs: $outLog / $errLog"
} finally { Pop-Location }
