Add-Type -AssemblyName System.Net.Http
Add-Type -AssemblyName System.Net.WebSockets
Add-Type -AssemblyName System.Runtime

\ = New-Object System.Net.HttpListener
\.Prefixes.Add("http://*:8080/")
\.Start()

Write-Host "Aegentis Router (PowerShell) online on port 8080"

while (\True) {
    \ = \.GetContext()
    if (\.Request.IsWebSocketRequest) {
        \ = \.AcceptWebSocketAsync().Result
        \ = \.WebSocket

        Write-Host "Twin connected"

        while (\.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
            \ = New-Object System.ArraySegment[byte] (1024)
            \ = \.ReceiveAsync(\, [System.Threading.CancellationToken]::None).Result

            \ = [System.Text.Encoding]::UTF8.GetString(\.Array, 0, \.Count)
            Write-Host "Received: \"

            \ = [System.Text.Encoding]::UTF8.GetBytes("Router ACK: \")
            \.SendAsync(
                (New-Object System.ArraySegment[byte] \),
                [System.Net.WebSockets.WebSocketMessageType]::Text,
                \True,
                [System.Threading.CancellationToken]::None
            ).Wait()
        }
    }
    else {
        \.Response.StatusCode = 403
        \.Response.Close()
    }
}
