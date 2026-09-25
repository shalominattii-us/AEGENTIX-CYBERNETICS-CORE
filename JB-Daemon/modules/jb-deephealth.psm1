function Invoke-JBDeepHealth {
    $report = [ordered]@{}

    # Windows-side health
    $report.WindowsOS      = (Get-CimInstance Win32_OperatingSystem).Caption
    $report.WindowsUptime  = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    $report.WindowsMemory  = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory

    # Kali-side health
    $report.KaliPing       = Invoke-JBSovereignRoute -Intent kali.ping
    $report.KaliUptime     = Invoke-JBSovereignRoute -Intent kali.health
    $report.KaliEnv        = Invoke-JBSovereignRoute -Intent kali.env

    return $report
}
