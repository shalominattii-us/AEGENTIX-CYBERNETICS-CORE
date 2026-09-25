Write-Host "Skill Registry online"

\ = "/skills"

if (Test-Path \) {
    Get-ChildItem \ -Filter *.ps1 | ForEach-Object {
        Write-Host "Loading skill: \"
        . \.FullName
    }
}
else {
    Write-Host "No skills directory found at \"
}

Write-Host "Skill Registry idle."
Start-Sleep -Seconds 3600
