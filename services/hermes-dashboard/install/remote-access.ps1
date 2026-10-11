<#
  remote-access.ps1 — give the unit (ROG Ally X, Windows 11 Home) unattended
  remote control, so the Hermes console and the agent stack can be driven from
  anywhere without touching the handheld.

  Why not plain Remote Desktop: the Ally X ships Windows 11 Home, which has the
  RDP *client* but no RDP *server*. You cannot connect INTO it with mstsc.
  This script installs the free, local-first equivalents instead:

    Tailscale  - private WireGuard mesh, unattended (survives logout/reboot).
                 Gives the unit a stable 100.x address reachable only by your
                 own devices. No ports opened to the internet.
    RustDesk   - full desktop control (screen, keyboard, mouse, file transfer),
                 installed as a service with a permanent password so it answers
                 while nobody is logged in. Can point at your own relay.
    Sunshine   - optional, low-latency GPU-encoded stream for when you want the
                 handheld's desktop to feel native (pair with Moonlight).

  Run elevated, from the repo root:
    powershell -ExecutionPolicy Bypass -File .\install\remote-access.ps1

  Flags:
    -RustDeskPassword <string>   permanent unattended password (prompted if omitted)
    -RustDeskRelay    <host>     your self-hosted relay, e.g. relay.mybox.net
    -RustDeskKey      <string>   that relay's public key
    -SkipTailscale               already on the tailnet
    -SkipSunshine                default; pass -WithSunshine to add it
    -WithSunshine
    -ExposeConsole               bind the Hermes console to the tailnet, not just localhost
#>

[CmdletBinding()]
param(
  [string]$RustDeskPassword,
  [string]$RustDeskRelay,
  [string]$RustDeskKey,
  [switch]$SkipTailscale,
  [switch]$WithSunshine,
  [switch]$ExposeConsole
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Say($msg, $tone = "Gray") { Write-Host "  $msg" -ForegroundColor $tone }
function Head($msg) { Write-Host "`n[$msg]" -ForegroundColor Cyan }

function Test-Admin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  (New-Object Security.Principal.WindowsPrincipal $id).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Admin)) {
  Write-Host "Must run elevated. Right-click PowerShell -> Run as administrator." -ForegroundColor Red
  exit 1
}

$stage = Join-Path $env:TEMP "hermes-remote"
New-Item -ItemType Directory -Force -Path $stage | Out-Null

function Have-Winget { $null -ne (Get-Command winget -ErrorAction SilentlyContinue) }

function Install-Pkg($wingetId, $label) {
  if (-not (Have-Winget)) { return $false }
  Say "winget install $wingetId"
  winget install --id $wingetId --exact --silent --accept-source-agreements --accept-package-agreements 2>&1 |
    Out-String | Write-Verbose
  if ($LASTEXITCODE -eq 0 -or $LASTEXITCODE -eq -1978335189) { Say "$label ok" Green; return $true }
  Say "winget returned $LASTEXITCODE for $label" Yellow
  return $false
}

# ---------------------------------------------------------------- Tailscale
if (-not $SkipTailscale) {
  Head "Tailscale — private mesh"
  $tsExe = "$env:ProgramFiles\Tailscale\tailscale.exe"
  if (-not (Test-Path $tsExe)) {
    if (-not (Install-Pkg "Tailscale.Tailscale" "Tailscale")) {
      $msi = Join-Path $stage "tailscale.msi"
      Say "downloading MSI directly"
      Invoke-WebRequest "https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi" -OutFile $msi
      Start-Process msiexec.exe -ArgumentList "/i `"$msi`" /qn /norestart" -Wait
    }
  } else { Say "already installed" Green }

  if (Test-Path $tsExe) {
    # --unattended is the whole point: the tunnel stays up with nobody logged in.
    Say "bringing the tunnel up unattended (a browser may open to authenticate)"
    & $tsExe up --unattended --accept-routes 2>&1 | Out-String | Write-Verbose
    Start-Sleep -Seconds 3
    $tsIp = (& $tsExe ip -4 2>$null | Select-Object -First 1)
    if ($tsIp) { Say "tailnet address: $tsIp" Green } else { Say "not authenticated yet — run: tailscale up --unattended" Yellow }
  } else {
    Say "Tailscale install failed — install manually from tailscale.com/download" Red
  }
}

# ---------------------------------------------------------------- RustDesk
Head "RustDesk — unattended desktop control"

if (-not $RustDeskPassword) {
  $sec = Read-Host "Permanent RustDesk password (min 8 chars, this is what you'll type to connect)" -AsSecureString
  $RustDeskPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec))
}
if ($RustDeskPassword.Length -lt 8) { Say "password under 8 chars — RustDesk will reject it" Red; exit 1 }

$rdExe = "$env:ProgramFiles\RustDesk\rustdesk.exe"
if (-not (Test-Path $rdExe)) {
  if (-not (Install-Pkg "RustDesk.RustDesk" "RustDesk")) {
    $api = Invoke-RestMethod "https://api.github.com/repos/rustdesk/rustdesk/releases/latest"
    $asset = $api.assets | Where-Object { $_.name -like "*x86_64.exe" } | Select-Object -First 1
    if (-not $asset) { Say "could not locate a RustDesk x86_64 installer" Red; exit 1 }
    $exe = Join-Path $stage $asset.name
    Say "downloading $($asset.name)"
    Invoke-WebRequest $asset.browser_download_url -OutFile $exe
    Say "silent install"
    Start-Process $exe -ArgumentList "--silent-install" -Wait
  }
} else { Say "already installed" Green }

if (-not (Test-Path $rdExe)) { Say "RustDesk not found after install" Red; exit 1 }

# Service install makes it answer before/without an interactive login.
Say "registering the service"
Start-Process $rdExe -ArgumentList "--install-service" -Wait -ErrorAction SilentlyContinue
Start-Sleep -Seconds 4

Say "setting the permanent password"
Start-Process $rdExe -ArgumentList "--password `"$RustDeskPassword`"" -Wait

if ($RustDeskRelay) {
  # Self-hosted relay keeps the session off the public rendezvous servers.
  $cfgDir = "$env:APPDATA\RustDesk\config"
  New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
  $toml = @"
rendezvous_server = '$RustDeskRelay'
nat_type = 1
serial = 0

[options]
custom-rendezvous-server = '$RustDeskRelay'
relay-server = '$RustDeskRelay'
api-server = 'https://$RustDeskRelay'
key = '$RustDeskKey'
"@
  Set-Content -Path (Join-Path $cfgDir "RustDesk2.toml") -Value $toml -Encoding UTF8
  Say "pinned to relay $RustDeskRelay" Green
  Restart-Service -Name "RustDesk" -ErrorAction SilentlyContinue
}

$rdId = $null
try {
  $rdId = (& $rdExe --get-id 2>$null | Select-Object -First 1)
} catch { }
if ($rdId) { Say "RustDesk ID: $rdId" Green } else { Say "open the RustDesk window once to read its ID" Yellow }

# ---------------------------------------------------------------- Sunshine
if ($WithSunshine) {
  Head "Sunshine — low-latency stream"
  if (-not (Install-Pkg "LizardByte.Sunshine" "Sunshine")) {
    Say "install manually: github.com/LizardByte/Sunshine/releases" Yellow
  } else {
    Say "pair from Moonlight, then open https://localhost:47990 to set the web UI credentials" Gray
  }
}

# ---------------------------------------------------------------- Console reach
Head "Hermes console over the tunnel"

$portsFile = Join-Path (Split-Path $PSScriptRoot -Parent) ".runable\ports.json"
$webPort = 4200
if (Test-Path $portsFile) {
  try { $webPort = (Get-Content $portsFile -Raw | ConvertFrom-Json).website } catch { }
}

if ($ExposeConsole) {
  # Vite binds loopback by default; --host makes it answer on the tailnet IP.
  Say "firewall rule for TCP $webPort on private networks"
  New-NetFirewallRule -DisplayName "Hermes console $webPort" -Direction Inbound `
    -Action Allow -Protocol TCP -LocalPort $webPort -Profile Private `
    -ErrorAction SilentlyContinue | Out-Null
  Say "start it with:  bun run dev -- --host 0.0.0.0" Gray
  if ($tsIp) { Say "then reach it at http://$($tsIp):$webPort" Green }
} else {
  Say "console left on localhost only — reach it inside the RustDesk session," Gray
  Say "or re-run with -ExposeConsole to serve it on the tailnet." Gray
}

# ---------------------------------------------------------------- Summary
Head "Unit is remotely operable"
Write-Host ""
Say "Desktop control : RustDesk client -> ID $(if($rdId){$rdId}else{'<see RustDesk window>'}), the password you just set"
Say "Network         : $(if($tsIp){"tailnet $tsIp"}else{'tailnet pending auth'})"
Say "Survives reboot : RustDesk service + Tailscale unattended = yes"
Say "Console         : http://localhost:$webPort$(if($ExposeConsole -and $tsIp){"  |  http://$($tsIp):$webPort"})"
Write-Host ""
Say "Next: run .\install\bootstrap-unit.ps1 if you haven't, to bring up the stack." Cyan
Write-Host ""
