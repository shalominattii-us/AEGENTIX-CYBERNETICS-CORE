const WebSocket = require('ws');
const port = process.env.VR_PORT ? parseInt(process.env.VR_PORT,10) : 7777;
const wss = new WebSocket.Server({ port });
wss.on('connection', ws => {
  ws.send(JSON.stringify({
    type: 'GENESIS_INIT',
    payload: {
      handle: 'Sovereign_HEMPEROR',
      worldSeed: 'atomic',
      renderMode: 'blueprint'
    }
  }));
  ws.on('message', msg => {
    // echo for dev visibility
    try { console.log('[VR RX]', msg.toString()); } catch(e){}
  });
});
console.log('[VR] Atomic VR stream online on ws://localhost:' + port);
