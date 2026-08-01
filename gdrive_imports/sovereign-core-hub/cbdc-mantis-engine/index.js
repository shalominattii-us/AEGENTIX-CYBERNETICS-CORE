const express = require('express');
const app = express();
const PORT = process.env.PORT || 8081;
app.get('/health', (req, res) => res.json({ status: 'online', service: 'mantis', engine: 'v9.0' }));
app.post('/mint', (req, res) => res.json({ status: 'minted', timestamp: Date.now() }));
app.post('/burn', (req, res) => res.json({ status: 'burned', timestamp: Date.now() }));
app.listen(PORT, () => console.log(`[Mantis] CBDC engine on port ${PORT}`));