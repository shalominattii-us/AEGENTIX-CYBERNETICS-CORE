// os12-systemMetrics.js
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
