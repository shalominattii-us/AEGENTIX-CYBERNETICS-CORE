function Invoke-ESS7ForensicFS {
    param([string]$Path = "C:\Forensic\Evidence")

    Write-Host "[ESS7-FOR] Filesystem sweep on $Path"
    Get-ChildItem -Path $Path -Recurse -ErrorAction SilentlyContinue |
        Select-Object FullName, Length, LastWriteTime |
        Out-File "C:\Forensic\Output\fs_scan.txt"

    Write-Host "[ESS7-FOR] Filesystem scan written to C:\Forensic\Output\fs_scan.txt"
}

Export-ModuleMember -Function Invoke-ESS7ForensicFS
