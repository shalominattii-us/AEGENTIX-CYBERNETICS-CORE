Write-Host "[ESS7] Booting Full System..."

. "$PSScriptRoot\init.ps1"

Import-Module "$PSScriptRoot\01_Core\Core.psm1" -Force
Import-Module "$PSScriptRoot\02_Modules\mod.network.psm1" -Force
Import-Module "$PSScriptRoot\02_Modules\mod.identity.psm1" -Force
Import-Module "$PSScriptRoot\02_Modules\mod.forensic.core.psm1" -Force
Import-Module "$PSScriptRoot\02_Modules\mod.forensic.fs.psm1" -Force
Import-Module "$PSScriptRoot\02_Modules\mod.forensic.network.psm1" -Force
Import-Module "$PSScriptRoot\03_Wrappers\wrapper.bridge.psm1" -Force
Import-Module "$PSScriptRoot\03_Wrappers\wrapper.forensic.psm1" -Force
Import-Module "$PSScriptRoot\04_Federal\federal.core.psm1" -Force
Import-Module "$PSScriptRoot\04_Federal\federal.forensic.psm1" -Force
Import-Module "$PSScriptRoot\05_Sysmon\sysmon.engine.psm1" -Force

Write-Host "[ESS7] Full System Online."

Start-ESS7Core
Invoke-ESS7Network
Invoke-ESS7Identity
Invoke-ESS7ForensicCore
