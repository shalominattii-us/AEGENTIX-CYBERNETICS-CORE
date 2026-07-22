import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readdir, readFile, stat } from 'node:fs/promises';
import { join, extname } from 'node:path';
import { createHash } from 'node:crypto';
import type { CapabilityAsset } from './capability-indexer.js';

const execFileAsync = promisify(execFile);
const zones: CapabilityAsset['executionZones']=['OpenClaw','Nemotron','Hermes','Docker','Manus'];
const hash=(value:unknown)=>createHash('sha256').update(JSON.stringify(value)).digest('hex');
export interface CapabilityCollector { collect(): Promise<CapabilityAsset[]>; }

export class DockerCapabilityCollector implements CapabilityCollector {
  async collect(): Promise<CapabilityAsset[]> {
    const { stdout } = await execFileAsync('docker', ['ps','-a','--format','{{json .}}']);
    return stdout.split(/\r?\n/).filter(Boolean).map((line) => {
      const row = JSON.parse(line); const name = row.Names ?? row.Image; const uri=`docker://${row.Image}/${name}`;
      return {id:`docker:${hash(uri).slice(0,20)}`,name,tags:tokenize(`${name} ${row.Image} ${row.Ports} ${row.Status}`),maturity:/Up /.test(row.Status??'')?'deployed':'image',evidence:[uri,row.Status].filter(Boolean),executionZones:zones,sourceType:'docker',sourceUri:uri,description:`Docker container ${name} using image ${row.Image}`,metadata:row,contentHash:hash(row),discoveredAt:new Date().toISOString()} satisfies CapabilityAsset;
    });
  }
}

export class GitHubWorkspaceCollector implements CapabilityCollector {
  constructor(private readonly roots: string[]) {}
  async collect(): Promise<CapabilityAsset[]> {
    const assets: CapabilityAsset[] = [];
    for (const root of this.roots) for (const entry of await safeReadDir(root)) {
      const full=join(root,entry.name); if(!entry.isDirectory()||!(await safeStat(join(full,'.git')))?.isDirectory()) continue;
      const readme=await readFirst(full,['README.md','README.MD','readme.md']);
      assets.push({id:`github:${hash(full).slice(0,20)}`,name:entry.name,tags:tokenize(`${entry.name} ${readme??''}`),maturity:'repository',evidence:[full],executionZones:zones,sourceType:'github',sourceUri:full,description:readme?.slice(0,600)??`Git repository at ${full}`,metadata:{path:full},contentHash:hash({full,readme}),discoveredAt:new Date().toISOString()});
    }
    return assets;
  }
}

export class FilesystemDocumentCollector implements CapabilityCollector {
  constructor(private readonly roots:string[],private readonly maxFiles=500){}
  async collect():Promise<CapabilityAsset[]>{const assets:CapabilityAsset[]=[];for(const root of this.roots)await walk(root,async path=>{if(assets.length>=this.maxFiles)return;const extension=extname(path).toLowerCase();if(!['.md','.txt','.json','.yaml','.yml','.pdf','.docx','.pptx','.step','.stp','.dwg'].includes(extension))return;let preview='';if(['.md','.txt','.json','.yaml','.yml'].includes(extension))preview=(await readFile(path,'utf8')).slice(0,1200);const sourceType=extension==='.step'||extension==='.stp'||extension==='.dwg'?'cad':'document';assets.push({id:`document:${hash(path).slice(0,20)}`,name:path.split(/[\\/]/).pop()??path,tags:tokenize(`${path} ${preview}`),maturity:'documented',evidence:[path],executionZones:zones,sourceType,sourceUri:path,description:preview||`${extension.slice(1).toUpperCase()} asset`,metadata:{path,extension},contentHash:hash({path,preview}),discoveredAt:new Date().toISOString()});});return assets;}
}
async function walk(root:string,visit:(path:string)=>Promise<void>):Promise<void>{for(const entry of await safeReadDir(root)){const full=join(root,entry.name);if(entry.isDirectory())await walk(full,visit);else await visit(full);}}
async function safeReadDir(path:string){try{return await readdir(path,{withFileTypes:true});}catch{return [];}}
async function safeStat(path:string){try{return await stat(path);}catch{return undefined;}}
async function readFirst(root:string,names:string[]){for(const name of names){try{return await readFile(join(root,name),'utf8');}catch{}}return undefined;}
function tokenize(value:string):string[]{return [...new Set((value.toLowerCase().match(/[a-z0-9][a-z0-9._-]{2,}/g)??[]).filter(v=>v.length<64))].slice(0,80);}