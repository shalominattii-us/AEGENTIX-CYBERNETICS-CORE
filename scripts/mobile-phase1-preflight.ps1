#requires -Version 5.1
[CmdletBinding()]
param([switch]$RunPhoneDriverDoctor)
$ErrorActionPreference = "Continue"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $env:USERPROFILE "Aegentix\reports"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null
$report = Join-Path $outDir "mobile-phase1-preflight-$stamp.txt"
Start-Transcript -Path $report -Force | Out-Null
Write-Host "=== AEGENTIX MOBILE PHASE 1: READ-ONLY PREFLIGHT ===" -ForegroundColor Cyan
Write-Host "Host: $env:COMPUTERNAME"
Write-Host "Time: $(Get-Date -Format o)"
Write-Host "No software installation, settings changes, device enrollment, or device-control commands will be performed."
function Show-CommandVersion([string]$Name, [string[]]$VersionArgs = @("--version")) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { Write-Host "[MISSING] $Name"; return }
    Write-Host "[FOUND] $Name -> $($cmd.Source)"
    try { & $Name @VersionArgs 2>&1 | Select-Object -First 4 } catch { Write-Host "Version check failed: $_" }
}
Write-Host "--- Windows ---"
Get-CimInstance Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber, OSArchitecture | Format-List
Write-Host "--- Required tools ---"
Show-CommandVersion "node"
Show-CommandVersion "npm"
Show-CommandVersion "git"
Show-CommandVersion "adb" @("version")
Show-CommandVersion "phonedriver"
Write-Host "--- Android Platform Tools ---"
$adb = Get-Command adb -ErrorAction SilentlyContinue
if ($adb) {
    Write-Host "ADB path: $($adb.Source)"
    Write-Host "Connected-device listing (read-only):"
    & adb devices -l 2>&1
} else { Write-Host "[BLOCKED] adb is not on PATH." }
Write-Host "--- PhoneDriver package metadata (no install) ---"
$npm = Get-Command npm -ErrorAction SilentlyContinue
if ($npm) {
    try { npm view phonedriver version dist.integrity license engines.node --json 2>&1 }
    catch { Write-Host "npm registry metadata lookup failed: $_" }
}
$phone = Get-Command phonedriver -ErrorAction SilentlyContinue
if ($phone) {
    Write-Host "--- PhoneDriver doctor ---"
    if ($RunPhoneDriverDoctor) {
        Write-Warning "Doctor may download/cache the platform binary on first run."
        & phonedriver doctor 2>&1
    } else {
        Write-Host "Skipped. Use -RunPhoneDriverDoctor only after reviewing and approving the binary download."
    }
} else { Write-Host "[BLOCKED] PhoneDriver CLI is not installed. No package was installed by this preflight." }
Write-Host "--- AEGENTIX gateway listener check ---"
foreach ($port in @(8787, 8090)) {
    $listener = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
    if ($listener) { Write-Host "[LISTENING] TCP $port" } else { Write-Host "[NO LISTENER] TCP $port" }
}
Write-Host "Report saved to: $report"
Write-Host "Review before sharing; report may contain device serials and local paths."
Stop-Transcript | Out-Null
Write-Host "Preflight complete. No install or device-control action was performed." -ForegroundColor Green
Write-Host "Report: $report"
