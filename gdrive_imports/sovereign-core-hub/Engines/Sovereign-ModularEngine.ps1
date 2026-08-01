# Sovereign Modular Engine
param(
    [ValidateSet("full","backend","unity","clean")]
    [string]$Mode = "full"
)

$ErrorActionPreference = "Stop"
. "C:\Sovereign\Core\Sovereign-Core.ps1"

Write-Host "`n=== SOVEREIGN ENGINE: MODULAR ($Mode) ===`n" -ForegroundColor Cyan

Init-EnvCore

switch ($Mode) {
    "clean"   { Clean-StateCore }
    "backend" { Clean-StateCore; CORE-BuildBackend; CORE-BringUpSovereign; CORE-ShortcutsAndVersion }
    "unity"   { Clean-StateCore; CORE-BuildUnity; CORE-ShortcutsAndVersion }
    "full"    { Clean-StateCore; CORE-BuildBackend; CORE-BuildUnity; CORE-BringUpSovereign; CORE-ShortcutsAndVersion }
}

Write-Host "`n=== MODULAR ENGINE COMPLETE ($Mode) ===" -ForegroundColor Cyan
