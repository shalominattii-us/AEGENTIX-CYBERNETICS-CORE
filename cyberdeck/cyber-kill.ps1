param(
    [string]
)

if (-not ) {
    Write-Host "Usage: cyber-kill <container-name>"
    exit
}

docker rm -f 
Write-Host "Killed "
