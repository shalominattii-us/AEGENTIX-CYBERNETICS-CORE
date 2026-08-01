Add-Type -AssemblyName PresentationFramework
$theme = & (Join-Path (Split-Path $MyInvocation.MyCommand.Path) 'ESS7-ThemeEngine.ps1')
$window = New-Object System.Windows.Window
$window.WindowStyle='None'
$window.WindowState='Maximized'
$window.Topmost=$true
$window.Content='ESS7 COMMAND CENTER ? EXTENDED'
$window.ShowDialog() | Out-Null
