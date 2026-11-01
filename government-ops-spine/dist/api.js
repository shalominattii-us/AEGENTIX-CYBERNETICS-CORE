export const CYBERCORE_ROUTES = {
    ingest: 'POST /api/opportunities/ingest',
    analyze: 'POST /api/opportunities/:id/analyze',
    buildPlan: 'POST /api/opportunities/:id/build-plan',
    state: 'GET /api/opportunities/:id/state',
    health: 'GET /health'
};
