// os12-vrMetrics.js
function attachVrMetrics({ wss, app, label = 'Aegentis VR' } = {}) {
  const metrics = { wsConnections: 0, lastTick: Date.now() };

  setInterval(() => {
    const mem = process.memoryUsage();
    metrics.lastTick = Date.now();
    console.log(`[OS12.1][HEARTBEAT] ${label} alive | rss=${mem.rss} heap=${mem.heapUsed} ws=${metrics.wsConnections}`);
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
