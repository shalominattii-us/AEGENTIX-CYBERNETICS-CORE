Add-Type -AssemblyName System.Net.Http

\ = New-Object System.Net.HttpListener
\.Prefixes.Add("http://*:3000/")
\.Start()

Write-Host "Operator Console online at http://localhost:3000 (PowerShell)"

while (\True) {
    \ = \.GetContext()
    \ = "<html><body><h1>Aegentis Operator Console</h1><p>PowerShell Edition</p></body></html>"
    \ = [System.Text.Encoding]::UTF8.GetBytes(\)
    \.Response.OutputStream.Write(\, 0, \.Length)
    \.Response.Close()
}
