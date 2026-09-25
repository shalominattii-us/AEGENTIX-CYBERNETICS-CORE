param()

Write-Host ""
Write-Host "=== AEGENTIX CYBERDECK STATUS ===" -ForegroundColor Cyan

 = docker ps --format "{{.Names}} {{.Status}}"

foreach ( in ) {
     = .Split(" ")
     = [0]
     = ([1..(.Length-1)] -join " ")
    Write-Host ("{0,-35} {1}" -f , )
}

Write-Host ""
