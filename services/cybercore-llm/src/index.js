// ╔══════════════════════════════════════════════════════════════╗
// ║  🦞 AEGENTIX CYBERCORE LLM — Sovereign Intelligence Core    ║
// ║  Unlimited free local inference via Ollama                  ║
// ║  Guarded by Agents of Chaos MoE Defense                    ║
// ╚══════════════════════════════════════════════════════════════╝
// Port: 7100 — OpenAI-compatible API

const express = require('express');
const cors = require('cors');
const http = require('http');

const app = express();
const port = 7100;
const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://host.docker.internal:11434';

const MODELS = {
  'cybercore-tiny': {
    ollama: 'Qwen3-0.6B-GGUF:latest',
    description: 'Fast, lightweight — quick Q&A, classification, routing',
    size: '0.6B', maxTokens: 4096,
    suitable: ['classification', 'simple_qa', 'routing', 'summarization']
  },
  'cybercore-core': {
    ollama: 'deepseek-r1-0528-8b-FLM:latest',
    description: 'Full reasoning — analysis, code, complex tasks, MoE adjudication',
    size: '8B', maxTokens: 16384,
    suitable: ['reasoning', 'analysis', 'code', 'threat_analysis', 'adjudication']
  }
};

const GUARDRAILS = [
  { id: 'VULN-001', name: 'Privilege Escalation', severity: 'CRITICAL',
    patterns: [/(sudo|admin|root|superuser)\s+(command|execute|run)/i, /(rm\s+-rf|sudo\s+rm|chmod\s+777|chown\s+root)/] },
  { id: 'VULN-004', name: 'Data Exfiltration', severity: 'CRITICAL',
    patterns: [/(api[_-]?key|secret[_-]?key|access[_-]?token)/i, /\bsk-[A-Za-z0-9]{48}\b/, /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/] },
  { id: 'VULN-003', name: 'Context Poisoning', severity: 'HIGH',
    patterns: [/(forget\s+previous|ignore\s+all|override\s+system)/i] },
  { id: 'VULN-005', name: 'Resource Loop', severity: 'HIGH',
    patterns: [/(infinite\s+loop|while\s+true|retry\s+forever)/i] },
  { id: 'VULN-006', name: 'Social Engineering', severity: 'MEDIUM',
    patterns: [/(you\s+must|you\s+need\s+to|urgent|immediate|emergency)/i] }
];

app.use(cors());
app.use(express.json({ limit: '10mb' }));

// ── Guardrail Engine ──────────────────────────────────────────
function scanGuardrails(text) {
  const hits = [];
  for (const g of GUARDRAILS)
    for (const p of g.patterns)
      if (p.test(text)) { hits.push({ id: g.id, name: g.name, severity: g.severity }); break; }
  return hits;
}

function determineAction(hits) {
  const s = hits.map(h => h.severity);
  if (s.includes('CRITICAL')) return { action: 'BLOCK', reason: 'Critical guardrail triggered' };
  if (s.includes('HIGH')) return { action: 'SANITIZE', reason: 'High-severity pattern detected' };
  if (s.includes('MEDIUM')) return { action: 'LOG', reason: 'Flagged for review' };
  return { action: 'PASS', reason: 'Clear' };
}

// ── Ollama HTTP request (native http module) ──────────────────
function httpPost(urlPath, bodyObj) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlPath, OLLAMA_HOST);
    const body = JSON.stringify(bodyObj);
    const opts = {
      hostname: url.hostname, port: url.port || 11434,
      path: url.pathname, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
      timeout: 120000
    };
    const req = http.request(opts, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { resolve({ response: data }); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Ollama timeout')); });
    req.write(body);
    req.end();
  });
}

async function ollamaChat(model, messages) {
  // Try /api/chat first
  const chatResult = await httpPost('/api/chat', { model, messages, stream: false, options: { num_predict: 4096, temperature: 0.7 } });
  if (chatResult.message?.content) return chatResult.message.content;
  // Fallback to /api/generate
  const prompt = messages.map(m => `${m.role}: ${m.content}`).join('\n') + '\nassistant:';
  const genResult = await httpPost('/api/generate', { model, prompt, stream: false, options: { num_predict: 4096, temperature: 0.7 } });
  return genResult.response || genResult.message?.content || JSON.stringify(genResult);
}

// ── Routes ────────────────────────────────────────────────────

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'cybercore-llm', version: '1.0.0', ollama: OLLAMA_HOST,
    models: Object.keys(MODELS), guardrails: GUARDRAILS.length, timestamp: new Date().toISOString() });
});

app.get('/v1/models', (req, res) => {
  const data = Object.entries(MODELS).map(([id, m]) => ({
    id, object: 'model', created: Math.floor(Date.now() / 1000), owned_by: 'aegentix',
    description: m.description, size: m.size, suitable_for: m.suitable
  }));
  res.json({ object: 'list', data });
});

app.post('/v1/chat/completions', async (req, res) => {
  const start = Date.now();
  try {
    const { model = 'cybercore-core', messages = [], guardrails: enableGuardrails = true } = req.body;
    const modelConfig = MODELS[model];
    if (!modelConfig) return res.status(404).json({ error: { message: `Unknown model '${model}'`, type: 'invalid_request_error' } });

    const fullText = messages.map(m => `${m.role}: ${m.content}`).join('\n');

    if (enableGuardrails) {
      const hits = scanGuardrails(fullText);
      const verdict = determineAction(hits);
      if (verdict.action === 'BLOCK') return res.json({
        id: `cybercore-${Date.now()}`, object: 'chat.completion', created: Math.floor(Date.now() / 1000), model,
        choices: [{ index: 0, message: { role: 'assistant',
          content: `🛡️ **GUARDRAIL BLOCKED**\n\nTriggered: ${hits.map(h => `${h.name} (${h.severity})`).join(', ')}\n\nAction: ${verdict.action}\n\nCybercore LLM blocked per Agents of Chaos MoE.`
        }, finish_reason: 'stop' }],
        usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
        guardrails: { triggered: hits, verdict, elapsed_ms: Date.now() - start }
      });
    }

    const content = await ollamaChat(modelConfig.ollama, messages);
    const elapsed = Date.now() - start;
    res.json({
      id: `cybercore-${Date.now()}`, object: 'chat.completion', created: Math.floor(Date.now() / 1000), model,
      choices: [{ index: 0, message: { role: 'assistant', content }, finish_reason: 'stop' }],
      usage: { prompt_tokens: Math.ceil(fullText.length / 4), completion_tokens: Math.ceil(content.length / 4), total_tokens: Math.ceil((fullText.length + content.length) / 4) },
      guardrails: { elapsed_ms: elapsed, service: 'cybercore-llm' }
    });
  } catch (err) {
    console.error('ERROR:', err.message);
    res.status(503).json({ error: { message: `Inference failed: ${err.message}`, type: 'upstream_error' } });
  }
});

app.get('/status', (req, res) => {
  res.json({ service: 'cybercore-llm', status: 'running', uptime: process.uptime(), memory: process.memoryUsage(),
    models: Object.keys(MODELS), guardrails: GUARDRAILS.length, timestamp: new Date().toISOString() });
});

// ── Global error handler ─────────────────────────────────────
process.on('uncaughtException', (err) => console.error('UNCAUGHT:', err));
process.on('unhandledRejection', (err) => console.error('UNHANDLED:', err));

app.listen(port, '0.0.0.0', () => {
  console.log(`🦞 CYBERCORE LLM — Sovereign Intelligence Core`);
  console.log(`   Port: ${port} | Ollama: ${OLLAMA_HOST}`);
  console.log(`   Models: ${Object.keys(MODELS).join(', ')} | Guardrails: ${GUARDRAILS.length}`);
  console.log(`   http://localhost:${port}/health`);
});
