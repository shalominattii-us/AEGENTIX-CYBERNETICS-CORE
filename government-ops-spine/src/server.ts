import http from 'node:http';
import { Pool } from 'pg';
import { PostgresOpportunityRepository } from './postgres.js';
import { GovernmentOpsRuntime } from './runtime.js';

const port = Number(process.env.PORT ?? 8099);
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
const repository = new PostgresOpportunityRepository(pool);
const runtime = new GovernmentOpsRuntime(repository);

const server = http.createServer(async (req, res) => {
  if (req.url === '/health') {
    try {
      await pool.query('select 1');
      res.writeHead(200, { 'content-type': 'application/json' });
      return res.end(JSON.stringify({ ok: true, service: 'government-ops-spine', zones: ['OpenClaw','Nemotron','Hermes','Docker','Manus'] }));
    } catch (error) {
      res.writeHead(503, { 'content-type': 'application/json' });
      return res.end(JSON.stringify({ ok: false, error: error instanceof Error ? error.message : String(error) }));
    }
  }

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(Buffer.from(chunk));
  let body: unknown;
  if (chunks.length) {
    try { body = JSON.parse(Buffer.concat(chunks).toString('utf8')); }
    catch { res.writeHead(400, { 'content-type': 'application/json' }); return res.end(JSON.stringify({ error: 'Invalid JSON body' })); }
  }
  const response = await runtime.handle({ method: req.method ?? 'GET', path: (req.url ?? '/').split('?')[0], body });
  res.writeHead(response.status, { 'content-type': 'application/json' });
  res.end(JSON.stringify(response.body));
});

const shutdown = async () => { server.close(); await pool.end(); process.exit(0); };
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
server.listen(port, '0.0.0.0', () => console.log(JSON.stringify({ event: 'government_ops_spine.started', port })));
