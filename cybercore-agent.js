const http = require('http');
const readline = require('readline');

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

function ask(query) {
  return new Promise((resolve) => {
    const data = JSON.stringify({
      model: 'cybercore-tiny',
      messages: [{ role: 'user', content: query }]
    });
    const req = http.request({
      hostname: 'localhost', port: 7100, path: '/v1/chat/completions',
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, (res) => {
      let body = '';
      res.on('data', (c) => body += c);
      res.on('end', () => {
        if (!body) return resolve('[Empty - blocked or loading]');
        try { resolve(JSON.parse(body).choices[0].message.content); }
        catch { resolve('[Raw] ' + body); }
      });
    });
    req.on('error', (e) => resolve('[Error] ' + e.message));
    req.setTimeout(120000, () => { req.destroy(); resolve('[Timeout]'); });
    req.write(data);
    req.end();
  });
}

console.log('Aegentix + CyberCore');
console.log('Type "exit" to quit');
console.log('');

function loop() {
  rl.question('You: ', async (i) => {
    if (i === 'exit') { rl.close(); return; }
    console.log('AI:', await ask(i));
    loop();
  });
}
loop();
