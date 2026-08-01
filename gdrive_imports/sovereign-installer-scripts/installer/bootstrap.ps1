# SovereignInstaller.ps1
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$InstallerRoot = Join-Path $ScriptRoot "installer"

Write-Host "Ω Sovereign Installer" -ForegroundColor Cyan

& (Join-Path $InstallerRoot "bootstrap.ps1")

