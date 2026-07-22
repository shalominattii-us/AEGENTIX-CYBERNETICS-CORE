import { createHash } from 'node:crypto';
import type { CapabilityRecord, TreasuryAnalysis, CapabilityMatch, BrainPlan } from './types.js';
import { matchCapabilities } from './pipeline.js';

export type CapabilitySourceType='github'|'docker'|'document'|'service'|'cad'|'patent'|'test'|'manual';
export interface CapabilityAsset extends CapabilityRecord { sourceType:CapabilitySourceType; sourceUri:string; description:string; metadata:Record<string,unknown>; contentHash:string; discoveredAt:string; }
export interface CapabilitySource { name:string; scan():Promise<CapabilityAsset[]>; }
export interface CapabilityRegistry { upsert(asset:CapabilityAsset):Promise<void>; list():Promise<CapabilityAsset[]>; saveMatches(opportunityId:string,matches:CapabilityMatch[]):Promise<void>; }

const zones:CapabilityRecord['executionZones']=['OpenClaw','Nemotron','Hermes','Docker','Manus'];
const hash=(value:unknown)=>createHash('sha256').update(JSON.stringify(value)).digest('hex');
const tags=(...values:string[])=>Array.from(new Set(values.flatMap(v=>v.toLowerCase().match(/[a-z0-9][a-z0-9-]{2,}/g)??[]))).sort();

export class StaticCapabilitySource implements CapabilitySource {
 constructor(public readonly name:string,private readonly assets:Omit<CapabilityAsset,'contentHash'|'discoveredAt'>[]){}
 async scan():Promise<CapabilityAsset[]>{return this.assets.map(a=>({...a,contentHash:hash(a),discoveredAt:new Date().toISOString()}));}
}

export function githubAsset(input:{fullName:string;description?:string;topics?:string[];language?:string;url:string;defaultBranch?:string}):CapabilityAsset{
 const evidence=[input.url]; const metadata={language:input.language,defaultBranch:input.defaultBranch,topics:input.topics??[]};
 return {id:`github:${input.fullName}`,name:input.fullName,tags:tags(input.fullName,input.description??'',...(input.topics??[]),input.language??''),maturity:'repository',evidence,executionZones:zones,sourceType:'github',sourceUri:input.url,description:input.description??'',metadata,contentHash:hash({input,metadata}),discoveredAt:new Date().toISOString()};
}

export function dockerAsset(input:{image:string;container?:string;status?:string;ports?:string[];labels?:Record<string,string>}):CapabilityAsset{
 const sourceUri=`docker://${input.image}${input.container?`/${input.container}`:''}`; const metadata={container:input.container,status:input.status,ports:input.ports??[],labels:input.labels??{}};
 return {id:`docker:${hash(sourceUri).slice(0,20)}`,name:input.container??input.image,tags:tags(input.image,input.container??'',input.status??'',...(input.ports??[]),...Object.values(input.labels??{})),maturity:input.status?.toLowerCase().includes('running')?'deployed':'image',evidence:[sourceUri],executionZones:zones,sourceType:'docker',sourceUri,description:`Docker capability from ${input.image}`,metadata,contentHash:hash({input,metadata}),discoveredAt:new Date().toISOString()};
}

export function documentAsset(input:{path:string;title:string;text:string;kind?:CapabilitySourceType}):CapabilityAsset{
 return {id:`document:${hash(input.path).slice(0,20)}`,name:input.title,tags:tags(input.title,input.text),maturity:'documented',evidence:[input.path],executionZones:zones,sourceType:input.kind??'document',sourceUri:input.path,description:input.text.slice(0,500),metadata:{path:input.path},contentHash:hash(input),discoveredAt:new Date().toISOString()};
}

export class CapabilityIndexer {
 constructor(private readonly registry:CapabilityRegistry,private readonly sources:CapabilitySource[]){}
 async run():Promise<{scanned:number;upserted:number;sourceCounts:Record<string,number>}>{let scanned=0,upserted=0;const sourceCounts:Record<string,number>={};for(const source of this.sources){const assets=await source.scan();sourceCounts[source.name]=assets.length;scanned+=assets.length;for(const asset of assets){await this.registry.upsert(asset);upserted++;}}return{scanned,upserted,sourceCounts};}
 async planWithCapabilities(opportunityId:string,analysis:TreasuryAnalysis,plan:BrainPlan){const capabilities=await this.registry.list();const matches=matchCapabilities(analysis,capabilities);await this.registry.saveMatches(opportunityId,matches);return{plan:{...plan,capabilityMatches:matches} as BrainPlan&{capabilityMatches:CapabilityMatch[]},matches};}
}

export class MemoryCapabilityRegistry implements CapabilityRegistry {
 private assets=new Map<string,CapabilityAsset>(); private matches=new Map<string,CapabilityMatch[]>();
 async upsert(asset:CapabilityAsset){this.assets.set(asset.id,asset);} async list(){return [...this.assets.values()];} async saveMatches(opportunityId:string,matches:CapabilityMatch[]){this.matches.set(opportunityId,matches);} getMatches(opportunityId:string){return this.matches.get(opportunityId)??[];}
}
