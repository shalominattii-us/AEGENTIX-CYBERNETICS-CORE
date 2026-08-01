const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 3000;
const staticPath = process.env.STATIC_PATH || path.join(__dirname, 'build');
app.use(express.static(staticPath));
app.get('*', (req, res) => res.sendFile(path.join(staticPath, 'index.html')));
app.listen(PORT, () => console.log(`[Dashboard] Sovereign console on port ${PORT}`));
// OS12.1_PATCHED
// OS12.1_PATCH
const { initPortalFusion } = require('../os12.1/os12-portalFusion');
const { attachSystemMetrics } = require('../os12.1/os12-systemMetrics');
const { registerRuntime } = require('../os12.1/os12-runtimeFederation');

initPortalFusion({ app });
attachSystemMetrics(app, { label: 'dashboard' });
registerRuntime('dashboard', {
  port: 3000,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});

// OS12.1_PATCHED
// OS12.1_PATCH
initPortalFusion({ app });
attachSystemMetrics(app, { label: 'dashboard' });

registerRuntime('dashboard', {
  port: 3000,
  handler: async ({ method, payload }) => ({ ok: true, method, payload })
});
