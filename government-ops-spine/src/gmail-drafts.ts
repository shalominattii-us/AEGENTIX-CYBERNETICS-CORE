import { createHash } from 'node:crypto';
import type { Pool } from 'pg';
import type { CorrespondenceDraft } from './correspondence.js';

export interface GmailDraftProvider {
  createDraft(input:{from:string;to:string[];cc:string[];subject:string;body:string;attachments:string[]}):Promise<{providerDraftId:string;createdAt:string}>;
}

export interface GmailDraftReceipt {
  receiptId:string;
  correspondenceId:string;
  providerDraftId:string;
  mailbox:string;
  createdAt:string;
  status:'draft_created';
  sendBlocked:true;
}

export class GmailDraftIntegration {
  constructor(private readonly pool:Pool){}

  async createReviewableDraft(correspondenceId:string,provider:GmailDraftProvider):Promise<GmailDraftReceipt>{
    const result=await this.pool.query('select * from correspondence_drafts where id=$1',[correspondenceId]);
    if(!result.rowCount)throw new Error('Correspondence draft not found.');
    const row=result.rows[0];
    if(row.status!=='approved')throw new Error('Gmail draft creation requires an approved single-message correspondence record.');
    const approval=await this.pool.query('select draft_id from correspondence_approvals where draft_id=$1',[correspondenceId]);
    if(!approval.rowCount)throw new Error('Approval receipt not found.');
    const draft:CorrespondenceDraft={id:row.id,purpose:row.purpose,mailbox:row.mailbox_json,to:row.to_json,cc:row.cc_json,subject:row.subject,body:row.body,attachments:row.attachments_json,opportunityId:row.opportunity_id??undefined,createdAt:new Date(row.created_at).toISOString(),status:row.status};
    const providerResult=await provider.createDraft({from:draft.mailbox.address,to:draft.to,cc:draft.cc,subject:draft.subject,body:draft.body,attachments:draft.attachments});
    const receiptBase={correspondenceId,providerDraftId:providerResult.providerDraftId,mailbox:draft.mailbox.address,createdAt:providerResult.createdAt,status:'draft_created' as const,sendBlocked:true as const};
    const receipt:GmailDraftReceipt={...receiptBase,receiptId:`GMAIL-${hash(receiptBase).slice(0,20)}`};
    await this.pool.query(`insert into gmail_draft_receipts(receipt_id,correspondence_id,provider_draft_id,mailbox,created_at,status,send_blocked) values($1,$2,$3,$4,$5,'draft_created',true) on conflict(correspondence_id) do update set provider_draft_id=excluded.provider_draft_id,mailbox=excluded.mailbox,created_at=excluded.created_at`,[receipt.receiptId,correspondenceId,receipt.providerDraftId,receipt.mailbox,receipt.createdAt]);
    await this.pool.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values('correspondence.gmail_draft.created',$1,$2)`,[correspondenceId,{receiptId:receipt.receiptId,providerDraftId:receipt.providerDraftId,sendBlocked:true}]);
    return receipt;
  }
}

export class DisabledGmailDraftProvider implements GmailDraftProvider {
  async createDraft():Promise<{providerDraftId:string;createdAt:string}>{throw new Error('Gmail provider is not configured. Draft creation remains blocked.');}
}

function hash(value:unknown){return createHash('sha256').update(JSON.stringify(value)).digest('hex');}
