module.exports = {
  apps: [
    { name: 'aegentis-vr', script: 'C:\\Sovereign\\aegentis-vr-backend\\vr-server.js', env: { PORT: 7777 }, autorestart: true },
    { name: 'dashboard',   script: 'C:\\Sovereign\\sovereign-dashboard-react\\server.js', env: { PORT: 3000 }, autorestart: true },
    { name: 'agentic-ai',  script: 'C:\\Sovereign\\agentic-ai-orchestrator\\main.py', interpreter: 'python', env: { PORT: 8844 }, autorestart: true },
    { name: 'destiny',     script: 'C:\\Sovereign\\destiny-custody-bridge\\index.js', env: { PORT: 9229 }, autorestart: true }
  ]
};
