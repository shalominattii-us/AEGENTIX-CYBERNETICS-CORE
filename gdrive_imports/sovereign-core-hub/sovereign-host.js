const http = require('http');
const fs = require('fs');
const path = require('path');
const PORT = 7788;
const FILE = path.join(__dirname, 'autoupdater.ps1');
http.createServer((req, res) => {
  if (req.url === '/autoupdater.ps1' && fs.existsSync(FILE)) {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    return res.end(fs.readFileSync(FILE, 'utf8'));
  }
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Sovereign Atomic Host OK');
}).listen(PORT, () => console.log('[HOST] Atomic host online at http://localhost:' + PORT));
