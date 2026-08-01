const express = require('express');
const app = express();
const PORT = process.env.PORT || 8080;
app.get('/health', (req, res) => res.json({ status: 'online', service: 'tsl', ledger: 'TSL_MAIN' }));
app.get('/balance/:address', (req, res) => res.json({ address: req.params.address, esc: 0, xrp: 0, timestamp: Date.now() }));
app.listen(PORT, () => console.log(`[TSL] Ledger interface on port ${PORT}`));
// OS12.1_PATCHED
// OS12.1_PATCH
attachSystemMetrics(app, { label: 'tsl-ledger' });

registerRuntime('tsl-ledger', {
  port: 9000,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});

// OS12.1_PATCHED
// OS12.1_PATCH
attachSystemMetrics(app, { label: 'tsl-ledger' });

registerRuntime('tsl-ledger', {
  port: 9000,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});
