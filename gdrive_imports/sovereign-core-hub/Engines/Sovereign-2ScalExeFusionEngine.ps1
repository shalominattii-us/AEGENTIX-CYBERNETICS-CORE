# Sovereign 2ScalExe Fusion Engine
param(
    [ValidateSet("full","backend","unity","clean")]
    [string]$Mode = "full"
)

$ErrorActionPreference = "Stop"
. "C:\Sovereign\Core\Sovereign-Core.ps1"

Write-Host "`n=== SOVEREIGN ENGINE: 2ScalExe FUSION ($Mode) ===`n" -ForegroundColor Cyan

Init-EnvCore

switch ($Mode) {
    "clean"   { Clean-StateCore }
    "backend" { Clean-StateCore; CORE-BuildBackend; CORE-BringUpSovereign }
    "unity"   { Clean-StateCore; CORE-BuildUnity }
    "full"    { Clean-StateCore; CORE-BuildBackend; CORE-BuildUnity; CORE-BringUpSovereign }
}

CORE-ShortcutsAndVersion

Write-Host "`n=== 2ScalExe FUSION ENGINE COMPLETE ($Mode) ===" -ForegroundColor Cyan
