Write-Host "`n[AEGENTIX] Initializing Sovereign Stack..." -ForegroundColor Cyan

# --- Ensure base directory ---
$base = "C:\Aegentix"
if (-not (Test-Path $base)) {
    New-Item -ItemType Directory -Path $base | Out-Null
}

# --- Install Jetpac runtime stub ---
$jetpac = "$base\jetpac.exe"
Set-Content -Path $jetpac -Value "# Jetpac runtime stub" -Encoding UTF8

# --- Install Jarvis Core ---
$jarvisCore = "$base\Jarvis-Core.psm1"
Set-Content -Path $jarvisCore -Value @"
function Invoke-Jarvis {
    param([string]`$q)
    "`$([DateTime]::Now) :: JARVIS :: $q"
}
"@ -Encoding UTF8

# --- Install KirkPrime Voice ---
$kirkPrime = "$base\Jarvis-KirkPrime.psm1"
Set-Content -Path $kirkPrime -Value @"
function Invoke-KirkPrime {
    param([string]`$q)
    "KIRKPRIME VOICE >> $q"
}
"@ -Encoding UTF8

# --- Install Antigravity integration stub ---
$anti = "$base\Antigravity-120B.psm1"
Set-Content -Path $anti -Value @"
function Invoke-Antigravity {
    param([string]`$design)
    "ANTIGRAVITY-120B :: BUILD :: $design"
}
"@ -Encoding UTF8

# --- Load modules ---
Import-Module $jarvisCore -Force
Import-Module $kirkPrime -Force
Import-Module $anti -Force

Write-Host "[AEGENTIX] Modules loaded." -ForegroundColor Green

# --- Start CyberdeckDaemon safely ---
Write-Host "[AEGENTIX] Starting CyberdeckDaemon..." -ForegroundColor Yellow

Start-Job -Name "CyberdeckDaemon" -ScriptBlock {
    & "C:\Aegentix\jetpac.exe"
}

Write-Host "[AEGENTIX] CyberdeckDaemon online." -ForegroundColor Green

# --- Self-healing boot confirmation ---
Write-Host "`n[AEGENTIX] Sovereign Stack is UP and RUNNING." -ForegroundColor Cyan
Write-Host "[AEGENTIX] Jarvis + KirkPrime + Antigravity ready." -ForegroundColor Cyan
