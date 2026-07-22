import { createHash } from 'node:crypto';
import type { Pool } from 'pg';
import type { ReviewerRole } from './artifact-review.js';

export type ReviewItemType='artifact_review'|'correspondence_review'|'gmail_draft_review'|'submission_package_review';
export type ReviewItemStatus='pending'|'approved'|'denied'|'changes_requested';
export interface OrganizationContact { organizationId:string; name:string; submissionEmail:string; cc:string[]; address?:string; jurisdiction?:string; sectors:string[]; verifiedAt:string; source:string; }
export interface ReviewQueueItem { reviewId:string; itemType:ReviewItemType; aggregateId:string; opportunityId?:string; title:string; summary:string; requiredRole:ReviewerRole|'executive'; status:ReviewItemStatus; dueAt?:string; createdAt:string; payload:Record<string,unknown>; }
export interface ReviewDecisionInput { decision:'approve'|'deny'|'request_changes'; decidedBy:string; role:ReviewerRole|'executive'; comments:string; authorizationToken:string; decidedAt:string; }
export interface SubmissionAttachment { packageId:string; filename:string; mediaType:string; contentBase64:string; contentHash:string; artifactId:string; }
export interface CompleteSubmissionPackage { packageId:string; opportunityId:string; programId:string; organization:OrganizationContact; subject:string; body:string; attachments:SubmissionAttachment[]; manifestId:string; createdAt:string; packageHash:string; status:'pending_review'|'approved'|'denied'; externalActionBlocked:true; }

export class CollaborationFlowService {
  constructor(private readonly pool:Pool){}

  async upsertOrganization(contact:OrganizationContact){
    validateEmail(contact.submissionEmail);
    await this.pool.query(`insert into organization_directory(organization_id,name,submission_email,cc_json,address,jurisdiction,sectors_json,verified_at,source) values($1,$2,$3,$4,$5,$6,$7,$8,$9) on conflict(organization_id) do update set name=excluded.name,submission_email=excluded.submission_email,cc_json=excluded.cc_json,address=excluded.address,jurisdiction=excluded.jurisdiction,sectors_json=excluded.sectors_json,verified_at=excluded.verified_at,source=excluded.source`,[contact.organizationId,contact.name,contact.submissionEmail,contact.cc,contact.address??null,contact.jurisdiction??null,contact.sectors,contact.verifiedAt,contact.source]);
    return contact;
  }

  async listOrganizations(){const r=await this.pool.query('select * from organization_directory order by name');return r.rows;}

  async reviewInbox(status:ReviewItemStatus='pending'){
    const r=await this.pool.query('select * from human_review_queue where status=$1 order by due_at nulls last,created_at',[status]);
    return {status,count:r.rowCount??0,items:r.rows};
  }

  async enqueue(input:Omit<ReviewQueueItem,'reviewId'|'status'|'createdAt'>):Promise<ReviewQueueItem>{
    const createdAt=new Date().toISOString();const base={...input,createdAt};const reviewId=`REVIEWQ-${hash(base).slice(0,20)}`;
    const item:ReviewQueueItem={reviewId,status:'pending',...base};
    await this.pool.query(`insert into human_review_queue(review_id,item_type,aggregate_id,opportunity_id,title,summary,required_role,status,due_at,payload_json,created_at) values($1,$2,$3,$4,$5,$6,$7,'pending',$8,$9,$10) on conflict(review_id) do nothing`,[reviewId,item.itemType,item.aggregateId,item.opportunityId??null,item.title,item.summary,item.requiredRole,item.dueAt??null,item.payload,createdAt]);
    await this.pool.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values('human.review.required',$1,$2)`,[reviewId,{reviewId,itemType:item.itemType,aggregateId:item.aggregateId,title:item.title,requiredRole:item.requiredRole}]);
    return item;
  }

  async decide(reviewId:string,input:ReviewDecisionInput){
    if(!input.authorizationToken.startsWith('AEGENTIX-AUTH-'))throw new Error('Explicit AEGENTIX authorization token required.');
    const status:ReviewItemStatus=input.decision==='approve'?'approved':input.decision==='deny'?'denied':'changes_requested';
    const tokenHash=createHash('sha256').update(input.authorizationToken).digest('hex');
    const client=await this.pool.connect();
    try{await client.query('begin');const updated=await client.query(`update human_review_queue set status=$2,decided_at=$3,decided_by=$4,decision_comments=$5,authorization_token_hash=$6 where review_id=$1 and status='pending' returning *`,[reviewId,status,input.decidedAt,input.decidedBy,input.comments,tokenHash]);if(!updated.rowCount)throw new Error('Review item not found or already decided.');await client.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values('human.review.decided',$1,$2)`,[reviewId,{reviewId,status,decidedBy:input.decidedBy,role:input.role}]);await client.query('commit');return updated.rows[0];}catch(e){await client.query('rollback');throw e;}finally{client.release();}
  }

  async assembleCompletePackage(input:{opportunityId:string;programId:string;organizationId:string;manifestId:string;subject?:string;body?:string}):Promise<CompleteSubmissionPackage>{
    const orgResult=await this.pool.query('select * from organization_directory where organization_id=$1',[input.organizationId]);if(!orgResult.rowCount)throw new Error('Organization contact not found.');
    const o=orgResult.rows[0];const organization:OrganizationContact={organizationId:o.organization_id,name:o.name,submissionEmail:o.submission_email,cc:o.cc_json,address:o.address??undefined,jurisdiction:o.jurisdiction??undefined,sectors:o.sectors_json,verifiedAt:new Date(o.verified_at).toISOString(),source:o.source};
    const exportsResult=await this.pool.query(`select e.package_id,e.filename,e.media_type,e.content_base64,e.content_hash,e.artifact_id from binary_artifact_exports e join engineering_artifacts a on a.artifact_id=e.artifact_id where a.program_id=$1 order by a.artifact_id,e.created_at desc`,[input.programId]);
    if(!exportsResult.rowCount)throw new Error('No rendered supporting documents found for this program.');
    const seen=new Set<string>();const attachments:SubmissionAttachment[]=[];for(const row of exportsResult.rows){if(seen.has(row.artifact_id))continue;seen.add(row.artifact_id);attachments.push({packageId:row.package_id,filename:row.filename,mediaType:row.media_type,contentBase64:row.content_base64,contentHash:row.content_hash,artifactId:row.artifact_id});}
    const createdAt=new Date().toISOString();const subject=input.subject??`Proposal submission — opportunity ${input.opportunityId}`;const body=input.body??`Dear ${organization.name} Review Team,\n\nPlease find attached the complete proposal package for opportunity ${input.opportunityId}. The package includes the proposal correspondence and all supporting technical, compliance, validation, manufacturing, and intellectual-property candidate documentation prepared for your review.\n\nThis message is a controlled draft and must receive explicit approval before transmission.\n\nRespectfully,\nAEGENTIX`;
    const base={opportunityId:input.opportunityId,programId:input.programId,organization,subject,body,attachments,manifestId:input.manifestId,createdAt,status:'pending_review' as const,externalActionBlocked:true as const};const packageHash=hash(base);const pkg:CompleteSubmissionPackage={...base,packageId:`SUBPKG-${packageHash.slice(0,20)}`,packageHash};
    await this.pool.query(`insert into complete_submission_packages(package_id,opportunity_id,program_id,organization_id,manifest_id,subject,body,attachments_json,package_hash,status,external_action_blocked,created_at) values($1,$2,$3,$4,$5,$6,$7,$8,$9,'pending_review',true,$10) on conflict(package_id) do nothing`,[pkg.packageId,pkg.opportunityId,pkg.programId,organization.organizationId,pkg.manifestId,pkg.subject,pkg.body,pkg.attachments,pkg.packageHash,pkg.createdAt]);
    await this.enqueue({itemType:'submission_package_review',aggregateId:pkg.packageId,opportunityId:pkg.opportunityId,title:`Review complete package for ${organization.name}`,summary:`${attachments.length} supporting documents; recipient ${organization.submissionEmail}`,requiredRole:'executive',payload:{packageId:pkg.packageId,organization,subject,attachmentCount:attachments.length,packageHash}});
    return pkg;
  }

  async getPackage(packageId:string){const r=await this.pool.query('select * from complete_submission_packages where package_id=$1',[packageId]);return r.rows[0];}
}
function validateEmail(value:string){if(!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value))throw new Error('Valid submission email required.');}
function hash(value:unknown){return createHash('sha256').update(JSON.stringify(value)).digest('hex');}
