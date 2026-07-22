export type CorrespondencePurpose = 'proposal'|'patent'|'partnership'|'clarification'|'general';
export interface OrganizationalMailbox { displayName:string; address:string; authorizedDomains?:string[]; }
export interface CorrespondenceDraft { id:string; purpose:CorrespondencePurpose; mailbox:OrganizationalMailbox; to:string[]; cc:string[]; subject:string; body:string; attachments:string[]; opportunityId?:string; createdAt:string; status:'draft'|'approved'|'sent'|'rejected'; approval?:ApprovalReceipt; }
export interface ApprovalReceipt { approvedBy:string; approvedAt:string; scope:'single_message'; authorizationToken:string; }
export interface CorrespondenceTransport { send(draft:CorrespondenceDraft):Promise<{providerMessageId:string;sentAt:string}>; }

export class CorrespondenceQueue {
  private readonly drafts=new Map<string,CorrespondenceDraft>();
  create(input:Omit<CorrespondenceDraft,'id'|'createdAt'|'status'>):CorrespondenceDraft{
    validateMailbox(input.mailbox);
    const id=`CORR-${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
    const draft:{id:string;createdAt:string;status:'draft'} & typeof input={id,createdAt:new Date().toISOString(),status:'draft',...input};
    this.drafts.set(id,draft);return draft;
  }
  approve(id:string,receipt:ApprovalReceipt):CorrespondenceDraft{
    if(!receipt.authorizationToken.startsWith('AEGENTIX-AUTH-'))throw new Error('Explicit AEGENTIX authorization token required.');
    const draft=this.require(id);const approved={...draft,status:'approved' as const,approval:receipt};this.drafts.set(id,approved);return approved;
  }
  async send(id:string,transport:CorrespondenceTransport):Promise<CorrespondenceDraft>{
    const draft=this.require(id);
    if(draft.status!=='approved'||!draft.approval)throw new Error('Correspondence blocked: approved single-message authorization required.');
    if(draft.purpose==='proposal'||draft.purpose==='patent')assertSubmissionAuthorized(draft.approval.authorizationToken);
    await transport.send(draft);const sent={...draft,status:'sent' as const};this.drafts.set(id,sent);return sent;
  }
  get(id:string){return this.drafts.get(id);}
  list(){return [...this.drafts.values()];}
  private require(id:string){const draft=this.drafts.get(id);if(!draft)throw new Error('Correspondence draft not found.');return draft;}
}

function validateMailbox(mailbox:OrganizationalMailbox):void{if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mailbox.address))throw new Error('A valid organizational mailbox is required.');}
function assertSubmissionAuthorized(token:string):void{if(!token.startsWith('AEGENTIX-AUTH-'))throw new Error('Proposal or patent submission blocked.');}
