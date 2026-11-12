import { readFileSync } from 'node:fs';

const placeholder = '00000000-0000-4000-8000-000000000001';
const config = readFileSync(new URL('../wrangler.jsonc', import.meta.url), 'utf8');
if (config.includes(placeholder)) {
  console.error('Replace database_id in wrangler.jsonc with the id from `wrangler d1 create opportunity-intake` before deploying.');
  process.exit(1);
}
