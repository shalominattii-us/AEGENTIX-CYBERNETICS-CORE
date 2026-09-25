param(
    [string]
)

if (-not ) {
    Write-Host "Usage: cyber-restart <container-name>"
    exit
}

docker restart 
Write-Host "Restarted "
