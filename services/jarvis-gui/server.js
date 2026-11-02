import express from 'express';
import { WebSocketServer } from 'ws';
import { createServer } from 'http';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const server = createServer(app);
const wss = new WebSocketServer({ server });

const PORT = process.env.JARVIS_GUI_PORT || 3000;

// Serve static files
app.use(express.static(path.join(__dirname, '../../gui/jarvis')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../../gui/jarvis/index.html'));
});

app.get('/api/status', (req, res) => {
  res.json({
    status: 'online',
    system: 'JARVIS',
    division: 'KERNEL',
    timestamp: new Date().toISOString(),
    zones: ['KERNEL', 'TREASURY', 'AI', 'SECURITY', 'XR', 'DATA', 'CLOUD', 'ORBITAL', 'FACTORY', 'SOVEREIGN']
  });
});

wss.on('connection', (ws) => {
  console.log('Client connected to JARVIS GUI');
  
  ws.send(JSON.stringify({
    type: 'welcome',
    message: 'JARVIS Online - All systems nominal'
  }));
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message.toString());
      console.log('Command received:', data);
      
      ws.send(JSON.stringify({
        type: 'response',
        message: `JARVIS: Processing command - ${data.command}`,
        timestamp: new Date().toISOString()
      }));
    } catch (e) {
      ws.send(JSON.stringify({
        type: 'error',
        message: 'Invalid command format'
      }));
    }
  });
  
  ws.on('close', () => {
    console.log('Client disconnected from JARVIS GUI');
  });
});

server.listen(PORT, () => {
  console.log(`JARVIS GUI running on http://localhost:${PORT}`);
});
