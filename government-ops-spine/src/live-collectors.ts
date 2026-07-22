import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readdir, readFile, stat } from 'node:fs/promises';
import { join, extname } from 'node:path';
import type { CapabilityAsset } from './capabilities.js';

const execFileAsync = promisify(execFile);

export interface CapabilityCollector { collect(): Promise<CapabilityAsset[]>; }

export class DockerCapabilityCollector implements CapabilityCollector {
  async collect(): Promise<CapabilityAsset[]> {
    const { stdout } = await execFileAsync('docker', ['ps','-a','--format','{{json .}}']);
    return stdout.split(/\r?\n/).filter(Boolean).map((line) => {
      const row = JSON.parse(line);
      const name = row.Names ?? row.Image;
      return {
        assetId: `docker:${name}`,
        kind: 'docker',
        name,
        description: `Docker container ${name} using image ${row.Image}`,
        tags: tokenize(`${name} ${row.Image} ${row.Ports} ${row.Status}`),
        maturity: /Up /.test(row.Status ?? '') ? 'operational' : 'experimental',
        evidence: [row.Image, row.Status].filter(Boolean),
        executionZones: ['Docker'],
        metadata: row
      } satisfies CapabilityAsset;
    });
  }
}

export class GitHubWorkspaceCollector implements CapabilityCollector {
  constructor(private readonly roots: string[]) {}
  async collect(): Promise<CapabilityAsset[]> {
    const assets: CapabilityAsset[] = [];
    for (const root of this.roots) {
      for (const entry of await safeReadDir(root)) {
        const full = join(root, entry.name);
        if (!entry.isDirectory()) continue;
        const git = await safeStat(join(full, '.git'));
        if (!git?.isDirectory()) continue;
        const readme = await readFirst(full, ['README.md','README.MD','readme.md']);
        assets.push({
          assetId: `github:${full}`,
          kind: 'github',
          name: entry.name,
          description: readme?.slice(0, 600) ?? `Git repository at ${full}`,
          tags: tokenize(`${entry.name} ${readme ?? ''}`),
          maturity: 'prototype',
          evidence: [full],
          executionZones: ['OpenClaw','Nemotron','Docker','Hermes','Manus'],
          metadata: { path: full }
        });
      }
    }
    return assets;
  }
}

export class FilesystemDocumentCollector implements CapabilityCollector {
  constructor(private readonly roots: string[], private readonly maxFiles = 500) {}
  async collect(): Promise<CapabilityAsset[]> {
    const assets: CapabilityAsset[] = [];
    for (const root of this.roots) await walk(root, async (path) => {
      if (assets.length >= this.maxFiles) return;
      const extension = extname(path).toLowerCase();
      if (!['.md','.txt','.json','.yaml','.yml','.pdf','.docx','.pptx','.step','.stp','.dwg'].includes(extension)) return;
      let preview = '';
      if (['.md','.txt','.json','.yaml','.yml'].includes(extension)) preview = (await readFile(path,'utf8')).slice(0,1200);
      assets.push({assetId:`document:${path}`,kind: extension === '.step' || extension === '.stp' || extension === '.dwg' ? 'cad' : 'document',name:path.split(/[\\/]/).pop() ?? path,description:preview || `${extension.slice(1).toUpperCase()} asset`,tags:tokenize(`${path} ${preview}`),maturity:'prototype',evidence:[path],executionZones:['OpenClaw','Nemotron','Hermes','Docker','Manus'],metadata:{path,extension}});
    });
    return assets;
  }
}

async function walk(root:string, visit:(path:string)=>Promise<void>):Promise<void>{for(const entry of await safeReadDir(root)){const full=join(root,entry.name);if(entry.isDirectory())await walk(full,visit);else await visit(full);}}
async function safeReadDir(path:string){try{return await readdir(path,{withFileTypes:true});}catch{return [];}}
async function safeStat(path:string){try{return await stat(path);}catch{return undefined;}}
async function readFirst(root:string,names:string[]){for(const name of names){try{return await readFile(join(root,name),'utf8');}catch{}}return undefined;}
function tokenize(value:string):string[]{return [...new Set((value.toLowerCase().match(/[a-z0-9][a-z0-9._-]{2,}/g)??[]).filter(v=>v.length<64))].slice(0,80);}
