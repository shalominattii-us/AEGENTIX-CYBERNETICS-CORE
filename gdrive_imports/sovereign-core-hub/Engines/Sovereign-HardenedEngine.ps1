# Sovereign Hardened Engine
param()

$ErrorActionPreference = "Stop"
. "C:\Sovereign\Core\Sovereign-Core.ps1"

Write-Host "`n=== SOVEREIGN ENGINE: HARDENED ===`n" -ForegroundColor Cyan

Init-EnvCore
Clean-StateCore
CORE-BuildBackend
CORE-BuildUnity
CORE-BringUpSovereign
CORE-ShortcutsAndVersion

Write-Host "`n=== HARDENED ENGINE COMPLETE ===" -ForegroundColor Cyan
