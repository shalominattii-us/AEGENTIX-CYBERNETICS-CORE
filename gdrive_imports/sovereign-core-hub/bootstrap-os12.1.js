// =====================================================
//   SOVEREIGN OS‑12.1 — FULL JS BUNDLE BOOTSTRAPPER
//   Generates all 5 bundles cleanly + atomically
// =====================================================

const fs = require('fs');
const path = require('path');

const root = "C:\\Sovereign";
const bundleDir = path.join(root, "os12.1");

if (!fs.existsSync(bundleDir)) {
  fs.mkdirSync(bundleDir, { recursive: true });
  console.log("[OS12.1][BOOTSTRAP] Created:", bundleDir);
}

// ------------------------------
// Bundle 1: Auto‑Shell‑Detect
// ------------------------------
fs.writeFileSync(
  path.join(bundleDir, "os12-autoShellDetect.js"),
`// os12-autoShellDetect.js
function detectShell() {
  const comspec = process.env.ComSpec || '';
  const isCmd = comspec.toLowerCase().includes('cmd.exe');
  const shellInfo = { comspec, isCmd, argv0: process.argv[0], platform: process.platform };
  console.log('[OS12.1][SHELL]', JSON.stringify(shellInfo));
  return shellInfo;
}
module.exports = { detectShell };
`
);

// ------------------------------
// Bundle 2: VR Metrics
// ------------------------------
fs.writeFileSync(
  path.join(bundleDir, "os12-vrMetrics.js"),
`// os12-vrMetrics.js
function attachVrMetrics({ wss, app, label = 'Aegentis VR' } = {}) {
  const metrics = { wsConnections: 0, lastTick: Date.now() };

  setInterval(() => {
    const mem = process.memoryUsage();
    metrics.lastTick = Date.now();
    console.log(\`[OS12.1][HEARTBEAT] \${label} alive | rss=\${mem.rss} heap=\${mem.heapUsed} ws=\${metrics.wsConnections}\`);
  }, 15000);

  if (wss && typeof wss.on === 'function') {
    wss.on('connection', socket => {
      metrics.wsConnections++;
      socket.on('close', () => metrics.wsConnections--);
    });
  }

  if (app && typeof app.get === 'function') {
    app.get('/metrics', (req, res) => {
      const mem = process.memoryUsage();
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({
        rss: mem.rss,
        heapUsed: mem.heapUsed,
        wsConnections: metrics.wsConnections,
        lastTick: metrics.lastTick,
        label
      }));
    });
  }

  return metrics;
}
module.exports = { attachVrMetrics };
`
);

// ------------------------------
// Bundle 3: Portal Fusion
// ------------------------------
fs.writeFileSync(
  path.join(bundleDir, "os12-portalFusion.js"),
`// os12-portalFusion.js
function initPortalFusion({ app, config = {} } = {}) {
  const state = {
    vrUrl: config.vrUrl || 'http://localhost:7777',
    dashboardUrl: config.dashboardUrl || 'http://localhost:3000',
    agenticUrl: config.agenticUrl || 'http://localhost:8844'
  };

  if (!app || typeof app.get !== 'function') {
    console.log('[OS12.1][PORTAL] No app provided, fusion idle.');
    return state;
  }

  app.get('/portal/fusion', (req, res) => {
    res.json({ ...state, version: 'os12.1' });
  });

  console.log('[OS12.1][PORTAL] Fusion active:', state);
  return state;
}
module.exports = { initPortalFusion };
`
);

// ------------------------------
// Bundle 4: Runtime Federation
// ------------------------------
fs.writeFileSync(
  path.join(bundleDir, "os12-runtimeFederation.js"),
`// os12-runtimeFederation.js
const registry = new Map();

function registerRuntime(name, info) {
  registry.set(name, { name, info, updatedAt: Date.now() });
  console.log('[OS12.1][FEDERATION] Registered:', name, info);
}

function listRuntimes() {
  return Array.from(registry.values());
}

async function callRuntime(name, method, payload) {
  const rt = registry.get(name);
  if (!rt || !rt.info || typeof rt.info.handler !== 'function') {
    throw new Error(\`Runtime \${name} unavailable\`);
  }
  return rt.info.handler({ method, payload });
}

module.exports = { registerRuntime, listRuntimes, callRuntime };
`
);

// ------------------------------
// Bundle 5: System Metrics
// ------------------------------
fs.writeFileSync(
  path.join(bundleDir, "os12-systemMetrics.js"),
`// os12-systemMetrics.js
function attachSystemMetrics(app, { label = 'service', extra = () => ({}) } = {}) {
  if (!app || typeof app.get !== 'function') {
    console.log('[OS12.1][METRICS] No app provided, idle.');
    return;
  }

  app.get('/metrics', (req, res) => {
    const mem = process.memoryUsage();
    const base = {
      label,
      rss: mem.rss,
      heapUsed: mem.heapUsed,
      uptime: process.uptime(),
      pid: process.pid,
      timestamp: Date.now()
    };

    let extraData = {};
    try { extraData = extra() || {}; } catch (e) { extraData = { extraError: e.message }; }

    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ ...base, ...extraData }));
  });

  console.log('[OS12.1][METRICS] /metrics attached for', label);
}
module.exports = { attachSystemMetrics };
`
);

// ------------------------------
console.log("🚀 OS‑12.1 JS Bundles Bootstrapped Successfully");

