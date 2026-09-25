import express from 'express';
import expressWs from 'express-ws';
import axios from 'axios';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
expressWs(app);

const PORT = process.env.PORT || 3000;
const RUNTIME_AGENT_URL = process.env.RUNTIME_AGENT_URL || 'http://aegentix-runtime:8080';
const GAIA_URL = process.env.GAIA_URL || 'http://aegentix-gaia:8090';

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

console.log(`[HUD] Starting on port ${PORT}`);
console.log(`[HUD] Runtime Agent: ${RUNTIME_AGENT_URL}`);
console.log(`[HUD] GAIA Node: ${GAIA_URL}`);

// API: Get agent status
app.get('/api/status', async (req, res) => {
  try {
    const response = await axios.get(`${RUNTIME_AGENT_URL}/status`, { timeout: 5000 });
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API: Get agent logs
app.get('/api/logs', async (req, res) => {
  try {
    const response = await axios.get(`${RUNTIME_AGENT_URL}/logs?limit=100`, { timeout: 5000 });
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API: Send directive
app.post('/api/directive', async (req, res) => {
  const { directive, goal, constraints } = req.body;

  try {
    const response = await axios.post(
      `${RUNTIME_AGENT_URL}/act`,
      { directive, goal, constraints },
      { timeout: 10000 }
    );
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// API: Get GAIA status
app.get('/api/gaia/status', async (req, res) => {
  try {
    const response = await axios.get(`${GAIA_URL}/health`, { timeout: 5000 });
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: err.message, status: 'offline' });
  }
});

// API: Get registered agents
app.get('/api/gaia/agents', async (req, res) => {
  try {
    const response = await axios.get(`${GAIA_URL}/agents`, { timeout: 5000 });
    res.json(response.data);
  } catch (err) {
    res.status(500).json({ error: err.message, agents: [] });
  }
});

// WebSocket: Real-time updates
app.ws('/ws/updates', (ws, req) => {
  console.log('[HUD] WebSocket client connected');

  const interval = setInterval(async () => {
    try {
      const status = await axios.get(`${RUNTIME_AGENT_URL}/status`, { timeout: 3000 });
      ws.send(JSON.stringify({ type: 'status', data: status.data }));
    } catch (err) {
      ws.send(JSON.stringify({ type: 'error', message: err.message }));
    }
  }, 2000);

  ws.on('close', () => {
    clearInterval(interval);
    console.log('[HUD] WebSocket client disconnected');
  });
});

app.listen(PORT, () => {
  console.log(`[HUD] Server listening on port ${PORT}`);
});
