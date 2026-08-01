function Invoke-ESS7ForensicSweep {
    Write-Host "[ESS7-FOR] Running combined forensic sweep..."
    Invoke-ESS7ForensicFS
    Invoke-ESS7ForensicNetwork
    Write-Host "[ESS7-FOR] Forensic sweep complete."
}

Export-ModuleMember -Function Invoke-ESS7ForensicSweep
