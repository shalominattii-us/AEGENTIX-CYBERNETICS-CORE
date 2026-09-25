import express from 'express';
import expressWs from 'express-ws';
import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import pinoHttp from 'pino-http';
import dotenv from 'dotenv';

dotenv.config();

const app = express();
expressWs(app);

const logger = pinoHttp();
app.use(logger);
app.use(express.json());

const PORT = process.env.PORT || 8080;
const LLM_ENDPOINT = process.env.LLM_ENDPOINT || 'http://localhost:11434/api/generate';
const MCP_REGISTRY_URL = process.env.MCP_REGISTRY_URL || 'http://mcp-registry:7071/tools';
const GAIA_URL = process.env.GAIA_URL || 'http://aegentix-gaia:8090';

// State management
const state = {
  agentId: uuidv4(),
  status: 'idle',
  activeTasks: [],
  mcpServers: [],
  logs: [],
  version: '1.0.0'
};

// Utility: log action
function logAction(action, details) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    action,
    details,
    taskId: state.activeTasks[0]?.id || 'none'
  };
  state.logs.push(logEntry);
  if (state.logs.length > 500) state.logs.shift();
  console.log(`[${action}]`, details);
}

// Utility: discover MCP servers
async function discoverMCPServers() {
  try {
    const response = await axios.get(MCP_REGISTRY_URL, { timeout: 5000 });
    state.mcpServers = response.data.tools || [];
    logAction('MCP_DISCOVERY', `Found ${state.mcpServers.length} MCP servers`);
    return state.mcpServers;
  } catch (err) {
    logAction('MCP_DISCOVERY_ERROR', err.message);
    return [];
  }
}

// Utility: call LLM
async function callLLM(prompt) {
  try {
    const response = await axios.post(LLM_ENDPOINT, {
      model: process.env.LLM_MODEL || 'llama2',
      prompt,
      stream: false
    }, { timeout: 30000 });
    return response.data.response || '';
  } catch (err) {
    logAction('LLM_ERROR', err.message);
    return '';
  }
}

// Utility: invoke MCP tool
async function invokeMCPTool(toolName, args) {
  const server = state.mcpServers.find(s => s.name === toolName);
  if (!server) {
    logAction('MCP_TOOL_NOT_FOUND', toolName);
    return { error: 'Tool not found' };
  }

  try {
    const response = await axios.post(server.endpoint, {
      tool: toolName,
      args
    }, { timeout: 10000 });
    logAction('MCP_TOOL_INVOKED', `${toolName} completed`);
    return response.data;
  } catch (err) {
    logAction('MCP_TOOL_ERROR', `${toolName}: ${err.message}`);
    return { error: err.message };
  }
}

// REST Endpoints

// GET /health
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    agentId: state.agentId,
    uptime: process.uptime(),
    version: state.version
  });
});

// GET /status
app.get('/status', (req, res) => {
  res.json({
    agentId: state.agentId,
    status: state.status,
    activeTasks: state.activeTasks,
    mcpServersCount: state.mcpServers.length,
    logsCount: state.logs.length
  });
});

// POST /act - Send directive to agent
app.post('/act', async (req, res) => {
  const { directive, goal, constraints } = req.body;

  if (!directive) {
    return res.status(400).json({ error: 'directive required' });
  }

  const taskId = uuidv4();
  const task = {
    id: taskId,
    directive,
    goal: goal || 'Execute directive',
    constraints: constraints || [],
    status: 'running',
    createdAt: new Date().toISOString(),
    result: null
  };

  state.activeTasks.push(task);
  logAction('DIRECTIVE_RECEIVED', directive);

  // Process asynchronously
  setImmediate(async () => {
    try {
      // 1. Call Directive Interpreter
      let interpretation = {};
      try {
        const interpResponse = await axios.post('http://aegentix-directive:7070/interpret', {
          directive,
          constraints
        }, { timeout: 5000 });
        interpretation = interpResponse.data;
      } catch (err) {
        logAction('INTERPRETER_ERROR', err.message);
      }

      // 2. Call LLM to plan
      const plan = await callLLM(`Goal: ${goal}\nDirective: ${directive}\nPlan the steps to achieve this goal.`);
      logAction('LLM_PLANNING', 'Plan generated');

      // 3. Discover MCP tools
      await discoverMCPServers();

      // 4. Execute tools
      const toolResults = [];
      for (const tool of state.mcpServers.slice(0, 2)) {
        const result = await invokeMCPTool(tool.name, { directive });
        toolResults.push(result);
      }

      // 5. Register with GAIA if available
      try {
        await axios.post(`${GAIA_URL}/register`, {
          agentId: state.agentId,
          status: 'active',
          tools: state.mcpServers.map(t => t.name)
        }, { timeout: 3000 });
        logAction('GAIA_REGISTERED', 'Agent registered with GAIA');
      } catch (err) {
        logAction('GAIA_REGISTRATION_FAILED', err.message);
      }

      task.status = 'completed';
      task.result = {
        interpretation,
        plan,
        toolResults
      };

      logAction('DIRECTIVE_COMPLETED', taskId);
    } catch (err) {
      task.status = 'failed';
      task.result = { error: err.message };
      logAction('DIRECTIVE_FAILED', err.message);
    }
  });

  res.json({
    taskId,
    status: 'accepted',
    directive
  });
});

// GET /logs
app.get('/logs', (req, res) => {
  const limit = parseInt(req.query.limit) || 50;
  res.json(state.logs.slice(-limit));
});

// WebSocket endpoint for real-time updates
app.ws('/updates', (ws, req) => {
  logAction('WS_CONNECTED', 'Client connected');

  const interval = setInterval(() => {
    ws.send(JSON.stringify({
      type: 'status_update',
      data: {
        status: state.status,
        activeTasks: state.activeTasks.length,
        mcpServers: state.mcpServers.length
      }
    }));
  }, 2000);

  ws.on('close', () => {
    clearInterval(interval);
    logAction('WS_DISCONNECTED', 'Client disconnected');
  });
});

// Startup
app.listen(PORT, async () => {
  console.log(`[RUNTIME_AGENT] Started on port ${PORT}`);
  logAction('STARTUP', `Runtime Agent v${state.version}`);
  
  // Discover MCP servers
  await discoverMCPServers();
});
