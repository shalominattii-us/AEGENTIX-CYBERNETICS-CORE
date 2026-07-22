import { createHash } from 'node:crypto';
import type { Pool } from 'pg';
import type { EngineeringArtifact, EngineeringArtifactType } from './engineering-program.js';
import type { ReviewerRole, ReviewDecision } from './artifact-review.js';

export interface ReviewSnapshot {
  artifactId:string;
  artifactHash:string;
  reviewerRole:ReviewerRole;
  reviewerId:string;
  decision:ReviewDecision;
  reviewedAt:string;
}

export interface ReleasePolicyResult {
  artifactId:string;
  artifactHash:string;
  requiredRoles:ReviewerRole[];
  approvedRoles:ReviewerRole[];
  missingRoles:ReviewerRole[];
  blockingDecisions:ReviewSnapshot[];
  releaseState:'internal_review'|'role_review_complete';
  externalActionBlocked:true;
}

export interface ExportManifestEntry {
  artifactId:string;
  artifactType:EngineeringArtifactType;
  artifactHash:string;
  approvalState:string;
  exportPackageIds:string[];
  releasePolicy:ReleasePolicyResult;
}

export interface EngineeringExportManifest {
  manifestId:string;
  programId:string;
  opportunityId:string;
  generatedAt:string;
  entries:ExportManifestEntry[];
  manifestHash:string;
  releaseState:'internal_review'|'role_review_complete';
  externalActionBlocked:true;
}

type ReleaseState=ReleasePolicyResult['releaseState'];

export function requiredRolesFor(type:EngineeringArtifactType):ReviewerRole[]{
  if(type==='patent_candidate_package')return ['technical','legal','executive'];
  if(type==='proposal_draft')return ['technical','compliance','executive'];
  if(type==='manufacturing_plan')return ['technical','manufacturing','compliance'];
  return ['technical','compliance'];
}

export function evaluateReleasePolicy(artifact:EngineeringArtifact,reviews:ReviewSnapshot[]):ReleasePolicyResult{
  const current=reviews.filter(r=>r.artifactId===artifact.artifactId&&r.artifactHash===artifact.contentHash);
  const latestByRole=new Map<ReviewerRole,ReviewSnapshot>();
  for(const review of current.sort((a,b)=>Date.parse(a.reviewedAt)-Date.parse(b.reviewedAt)))latestByRole.set(review.reviewerRole,review);
  const requiredRoles=requiredRolesFor(artifact.type);
  const approvedRoles=requiredRoles.filter(role=>latestByRole.get(role)?.decision==='approve');
  const missingRoles=requiredRoles.filter(role=>!approvedRoles.includes(role));
  const blockingDecisions=[...latestByRole.values()].filter(r=>r.decision!=='approve');
  const releaseState:ReleaseState=missingRoles.length===0&&blockingDecisions.length===0?'role_review_complete':'internal_review';
  return {artifactId:artifact.artifactId,artifactHash:artifact.contentHash,requiredRoles,approvedRoles,missingRoles,blockingDecisions,releaseState,externalActionBlocked:true};
}

export class ReleasePolicyService{
  constructor(private readonly pool:Pool){}

  async evaluateArtifact(artifactId:string):Promise<ReleasePolicyResult>{
    const artifactResult=await this.pool.query('select artifact_json from engineering_artifacts where artifact_id=$1',[artifactId]);
    if(!artifactResult.rowCount)throw new Error('Engineering artifact not found.');
    const artifact=artifactResult.rows[0].artifact_json as EngineeringArtifact;
    const reviewsResult=await this.pool.query(`select artifact_id,artifact_hash,reviewer_json->>'role' as reviewer_role,reviewer_json->>'reviewerId' as reviewer_id,decision,reviewed_at from artifact_reviews where artifact_id=$1 order by reviewed_at`,[artifactId]);
    const reviews:ReviewSnapshot[]=reviewsResult.rows.map(row=>({artifactId:String(row.artifact_id),artifactHash:String(row.artifact_hash),reviewerRole:String(row.reviewer_role) as ReviewerRole,reviewerId:String(row.reviewer_id),decision:String(row.decision) as ReviewDecision,reviewedAt:new Date(row.reviewed_at).toISOString()}));
    return evaluateReleasePolicy(artifact,reviews);
  }

  async createProgramManifest(programId:string):Promise<EngineeringExportManifest>{
    const programResult=await this.pool.query('select opportunity_id from engineering_programs where program_id=$1',[programId]);
    if(!programResult.rowCount)throw new Error('Engineering program not found.');
    const artifactsResult=await this.pool.query('select artifact_json,approval_state from engineering_artifacts where program_id=$1 order by artifact_id',[programId]);
    const entries:ExportManifestEntry[]=[];
    for(const row of artifactsResult.rows){
      const artifact=row.artifact_json as EngineeringArtifact;
      const exportsResult=await this.pool.query('select package_id from artifact_exports where artifact_id=$1 order by created_at',[artifact.artifactId]);
      entries.push({artifactId:artifact.artifactId,artifactType:artifact.type,artifactHash:artifact.contentHash,approvalState:String(row.approval_state),exportPackageIds:exportsResult.rows.map(r=>String(r.package_id)),releasePolicy:await this.evaluateArtifact(artifact.artifactId)});
    }
    const generatedAt=new Date().toISOString();
    const releaseState:ReleaseState=entries.length>0&&entries.every(e=>e.releasePolicy.releaseState==='role_review_complete')?'role_review_complete':'internal_review';
    const opportunityId=String(programResult.rows[0].opportunity_id);
    const base:{programId:string;opportunityId:string;generatedAt:string;entries:ExportManifestEntry[];releaseState:ReleaseState;externalActionBlocked:true}={programId,opportunityId,generatedAt,entries,releaseState,externalActionBlocked:true};
    const manifestHash=hash(base);
    const manifest:EngineeringExportManifest={...base,manifestId:`MANIFEST-${manifestHash.slice(0,20)}`,manifestHash};
    await this.pool.query(`insert into engineering_export_manifests(manifest_id,program_id,opportunity_id,manifest_json,manifest_hash,release_state,external_action_blocked,created_at) values($1,$2,$3,$4,$5,$6,true,$7) on conflict(manifest_id) do nothing`,[manifest.manifestId,programId,manifest.opportunityId,manifest,manifestHash,releaseState,generatedAt]);
    await this.pool.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values('engineering.export_manifest.created',$1,$2)`,[programId,{manifestId:manifest.manifestId,releaseState,externalActionBlocked:true}]);
    return manifest;
  }

  async getManifest(manifestId:string):Promise<EngineeringExportManifest|undefined>{const result=await this.pool.query('select manifest_json from engineering_export_manifests where manifest_id=$1',[manifestId]);return result.rows[0]?.manifest_json as EngineeringExportManifest|undefined;}
}

function hash(value:unknown){return createHash('sha256').update(JSON.stringify(value)).digest('hex');}
