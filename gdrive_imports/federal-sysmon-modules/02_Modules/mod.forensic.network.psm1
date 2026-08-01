function Invoke-ESS7ForensicNetwork {
    Write-Host "[ESS7-FOR] Capturing network connections..."

    Get-NetTCPConnection -ErrorAction SilentlyContinue |
        Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, State |
        Out-File "C:\Forensic\Output\net_scan.txt"

    Write-Host "[ESS7-FOR] Network scan written to C:\Forensic\Output\net_scan.txt"
}

Export-ModuleMember -Function Invoke-ESS7ForensicNetwork
