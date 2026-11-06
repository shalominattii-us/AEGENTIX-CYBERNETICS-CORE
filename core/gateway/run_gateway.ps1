param()
$ErrorActionPreference = 'Stop'
$core = 'C:\AEGENTIX-CYBERNETICS-CORE'
$env:PYTHONPATH = $core
# SOC2 local ROG profile: loopback-only, explicit noauth override when no API token is configured.
if (-not $env:AEGENTIX_API_TOKEN -and -not $env:AEGENTIX_MCP_TOKEN -and -not $env:AEGENTIX_ALLOW_LOCAL_NOAUTH) {
  $env:AEGENTIX_ALLOW_LOCAL_NOAUTH = '1'
  Write-Host "[gateway] AEGENTIX_ALLOW_LOCAL_NOAUTH=1 (loopback dev mode; set AEGENTIX_API_TOKEN for authenticated mode)"
}
$py = Join-Path $core '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
Set-Location -LiteralPath $core
Write-Host "Starting AEGENTIX gateway (Infinite Brain OS MCP mounted) with PYTHONPATH=$core"
& $py -m uvicorn core.gateway.server:app --host 127.0.0.1 --port 8000
