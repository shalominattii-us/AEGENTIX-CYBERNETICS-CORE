param(
    [Parameter(Mandatory=True)][string],
    [string] = "GET",
    [string] = ""
)

\ = "http://localhost:7072/\"
Write-Host "Invoking MCP HTTP: \ \"

if (\ -eq "GET") {
    Invoke-WebRequest -Uri \ -UseBasicParsing
} else {
    Invoke-WebRequest -Uri \ -Method \ -Body \ -UseBasicParsing
}
