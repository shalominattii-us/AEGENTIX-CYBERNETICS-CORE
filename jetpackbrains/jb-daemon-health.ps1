Write-Host "[HEALTH] Checking containers..." -ForegroundColor Yellow
docker ps

Write-Host "[HEALTH] Checking ports..." -ForegroundColor Yellow
7071,7072,7073,8080,8090,3000 | ForEach-Object {
    $r = Test-NetConnection -ComputerName "localhost" -Port $_
    Write-Host "Port $_: $($r.TcpTestSucceeded)"
}
