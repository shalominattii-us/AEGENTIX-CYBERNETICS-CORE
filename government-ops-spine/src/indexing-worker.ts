import type { CapabilityCollector } from './live-collectors.js';
import type { CapabilityRegistry } from './capability-indexer.js';

export interface IndexingHealth { running:boolean; lastStartedAt?:string; lastCompletedAt?:string; lastAssetCount:number; lastError?:string; }

export class CapabilityIndexingWorker {
  private timer?: NodeJS.Timeout;
  readonly health: IndexingHealth = { running:false, lastAssetCount:0 };
  constructor(private readonly registry:CapabilityRegistry, private readonly collectors:CapabilityCollector[], private readonly intervalMs=15*60_000) {}
  async runOnce():Promise<number>{
    if(this.health.running) throw new Error('Capability indexing is already running.');
    this.health.running=true; this.health.lastStartedAt=new Date().toISOString(); this.health.lastError=undefined;
    try { let count=0; for(const collector of this.collectors){for(const asset of await collector.collect()){await this.registry.upsert(asset);count++;}} this.health.lastAssetCount=count; this.health.lastCompletedAt=new Date().toISOString(); return count; }
    catch(error){this.health.lastError=error instanceof Error?error.message:String(error);throw error;}
    finally{this.health.running=false;}
  }
  start():void{if(this.timer)return;void this.runOnce().catch(()=>{});this.timer=setInterval(()=>void this.runOnce().catch(()=>{}),this.intervalMs);}
  stop():void{if(this.timer)clearInterval(this.timer);this.timer=undefined;}
}