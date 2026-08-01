// os12-portalFusion.js
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
