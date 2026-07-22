import { createHash } from 'node:crypto';
import type { Pool } from 'pg';
import type { CapabilityRegistry } from './capability-indexer.js';
import type { CapabilityIndexingWorker } from './indexing-worker.js';
import type { CorrespondenceDraft, ApprovalReceipt } from './correspondence.js';

export interface ControlRequest { method:string; path:string; body?:unknown; }
export interface ControlResponse { status:number; body:unknown; }

export class ControlPlaneRuntime {
  constructor(private readonly pool:Pool,private readonly registry:CapabilityRegistry,private readonly indexer:CapabilityIndexingWorker){}
  async handle(request:ControlRequest):Promise<ControlResponse|undefined>{
    if(request.method==='GET'&&request.path==='/api/capabilities') return {status:200,body:await this.registry.list()};
    if(request.method==='GET'&&request.path==='/api/indexing/health') return {status:200,body:this.indexer.health};
    if(request.method==='POST'&&request.path==='/api/indexing/run') return {status:202,body:{assetCount:await this.indexer.runOnce(),health:this.indexer.health}};
    if(request.method==='POST'&&request.path==='/api/correspondence/drafts') return {status:201,body:await this.createDraft(request.body as Omit<CorrespondenceDraft,'id'|'createdAt'|'status'>)};
    const approve=request.path.match(/^\/api\/correspondence\/([^/]+)\/approve$/);
    if(request.method==='POST'&&approve) return {status:200,body:await this.approve(decodeURIComponent(approve[1]),request.body as ApprovalReceipt)};
    const get=request.path.match(/^\/api\/correspondence\/([^/]+)$/);
    if(request.method==='GET'&&get){const row=await this.pool.query('select * from correspondence_drafts where id=$1',[decodeURIComponent(get[1])]);return row.rowCount?{status:200,body:row.rows[0]}:{status:404,body:{error:'Correspondence draft not found'}};}
    return undefined;
  }
  private async createDraft(input:Omit<CorrespondenceDraft,'id'|'createdAt'|'status'>){
    if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(input.mailbox.address)) throw new Error('A valid organizational mailbox is required.');
    const id=`CORR-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,createdAt=new Date().toISOString();
    await this.pool.query(`insert into correspondence_drafts(id,purpose,mailbox_json,to_json,cc_json,subject,body,attachments_json,opportunity_id,status,created_at) values($1,$2,$3,$4,$5,$6,$7,$8,$9,'draft',$10)`,[id,input.purpose,input.mailbox,input.to,input.cc,input.subject,input.body,input.attachments,input.opportunityId??null,createdAt]);
    return {id,createdAt,status:'draft',...input};
  }
  private async approve(id:string,receipt:ApprovalReceipt){
    if(!receipt.authorizationToken.startsWith('AEGENTIX-AUTH-')) throw new Error('Explicit AEGENTIX authorization token required.');
    const hash=createHash('sha256').update(receipt.authorizationToken).digest('hex');
    const client=await this.pool.connect();
    try{await client.query('begin');const updated=await client.query(`update correspondence_drafts set status='approved',updated_at=now() where id=$1 and status='draft' returning *`,[id]);if(!updated.rowCount)throw new Error('Draft not found or not approvable.');await client.query(`insert into correspondence_approvals(draft_id,approved_by,approved_at,scope,authorization_token_hash) values($1,$2,$3,'single_message',$4) on conflict(draft_id) do update set approved_by=excluded.approved_by,approved_at=excluded.approved_at,authorization_token_hash=excluded.authorization_token_hash`,[id,receipt.approvedBy,receipt.approvedAt,hash]);await client.query('commit');return updated.rows[0];}catch(error){await client.query('rollback');throw error;}finally{client.release();}
  }
}