param([string]$Theme='DarkOps')
switch ($Theme) {
    'DarkOps' { @{Background='#050608';Foreground='#F5F7FA';Accent='#00D1FF'} }
    'WhiteGold' { @{Background='#FDFBF7';Foreground='#1A1A1A';Accent='#C9A227'} }
    'TerminalGlass' { @{Background='#050608';Foreground='#00FF9C';Accent='#00D1FF'} }
    'RetroGreen' { @{Background='#020502';Foreground='#00FF00';Accent='#00AA00'} }
    default { @{Background='#101010';Foreground='#FFFFFF';Accent='#FF4081'} }
}
