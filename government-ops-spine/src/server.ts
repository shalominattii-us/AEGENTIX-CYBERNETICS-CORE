import http from 'node:http';
import { Pool } from 'pg';
import { PostgresOpportunityRepository } from './postgres.js';
import { GovernmentOpsRuntime } from './runtime.js';
import { PostgresCapabilityRegistry } from './capability-postgres.js';
import { DockerCapabilityCollector, FilesystemDocumentCollector, GitHubWorkspaceCollector } from './live-collectors.js';
import { CapabilityIndexingWorker } from './indexing-worker.js';
import { ControlPlaneRuntime } from './control-plane.js';

const port=Number(process.env.PORT??8099);
const pool=new Pool({connectionString:process.env.DATABASE_URL});
const repository=new PostgresOpportunityRepository(pool);
const runtime=new GovernmentOpsRuntime(repository);
const capabilityRegistry=new PostgresCapabilityRegistry(pool);
const roots=(process.env.CAPABILITY_ROOTS??'/workspace').split(',').map(v=>v.trim()).filter(Boolean);
const collectors=[new DockerCapabilityCollector(),new GitHubWorkspaceCollector(roots),new FilesystemDocumentCollector(roots,Number(process.env.CAPABILITY_MAX_FILES??500))];
const indexer=new CapabilityIndexingWorker(capabilityRegistry,collectors,Number(process.env.CAPABILITY_INDEX_INTERVAL_MS??900000));
const controls=new ControlPlaneRuntime(pool,capabilityRegistry,indexer);
if(process.env.CAPABILITY_INDEX_ENABLED!=='false')indexer.start();

const server=http.createServer(async(req,res)=>{
  const path=(req.url??'/').split('?')[0];
  if(path==='/health'){
    try{await pool.query('select 1');res.writeHead(200,{'content-type':'application/json'});return res.end(JSON.stringify({ok:true,service:'government-ops-spine',zones:['OpenClaw','Nemotron','Hermes','Docker','Manus'],indexing:indexer.health}));}
    catch(error){res.writeHead(503,{'content-type':'application/json'});return res.end(JSON.stringify({ok:false,error:error instanceof Error?error.message:String(error)}));}
  }
  const chunks:Buffer[]=[];for await(const chunk of req)chunks.push(Buffer.from(chunk));let body:unknown;
  if(chunks.length){try{body=JSON.parse(Buffer.concat(chunks).toString('utf8'));}catch{res.writeHead(400,{'content-type':'application/json'});return res.end(JSON.stringify({error:'Invalid JSON body'}));}}
  try{
    const request={method:req.method??'GET',path,body};
    const response=(await controls.handle(request))??(await runtime.handle(request));
    res.writeHead(response.status,{'content-type':'application/json'});res.end(JSON.stringify(response.body));
  }catch(error){res.writeHead(400,{'content-type':'application/json'});res.end(JSON.stringify({error:error instanceof Error?error.message:String(error)}));}
});
const shutdown=async()=>{indexer.stop();server.close();await pool.end();process.exit(0);};
process.on('SIGINT',shutdown);process.on('SIGTERM',shutdown);
server.listen(port,'0.0.0.0',()=>console.log(JSON.stringify({event:'government_ops_spine.started',port,indexingEnabled:process.env.CAPABILITY_INDEX_ENABLED!=='false',roots})));
