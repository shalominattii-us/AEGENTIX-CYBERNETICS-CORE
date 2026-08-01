Write-Host 'ESS7 LAUNCHER'
Write-Host '1) GUI'
Write-Host '2) Terminal'
$sel = Read-Host 'Select'
if ($sel -eq '1') { powershell -File (Join-Path $PSScriptRoot 'ESS7-GUI.ps1') }
if ($sel -eq '2') { Get-ChildItem $PSScriptRoot -Filter 'ESS7-*-Installer.ps1' }
