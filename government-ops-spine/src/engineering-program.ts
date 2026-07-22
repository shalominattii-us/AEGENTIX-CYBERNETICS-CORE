import { createHash } from 'node:crypto';
import type { BrainPlan, BuildSpecification, CapabilityMatch, TreasuryAnalysis } from './types.js';

export type EngineeringArtifactType =
  | 'architecture'
  | 'subsystems'
  | 'interfaces'
  | 'risk_register'
  | 'verification_plan'
  | 'simulation_plan'
  | 'manufacturing_plan'
  | 'documentation_plan'
  | 'patent_candidate_package'
  | 'proposal_draft';

export interface EngineeringArtifact {
  artifactId:string;
  opportunityId:string;
  specificationId:string;
  type:EngineeringArtifactType;
  title:string;
  content:Record<string,unknown>;
  contentHash:string;
  createdAt:string;
  approvalState:'draft'|'technical_review'|'authorized';
  externalActionBlocked:true;
}

export interface EngineeringProgram {
  programId:string;
  opportunityId:string;
  specificationId:string;
  planId:string;
  artifacts:EngineeringArtifact[];
  capabilityMatches:CapabilityMatch[];
  generatedAt:string;
  externalActionsBlocked:true;
}

export class EngineeringProgramGenerator {
  generate(input:{analysis:TreasuryAnalysis; specification:BuildSpecification; plan:BrainPlan; capabilityMatches?:CapabilityMatch[]}):EngineeringProgram {
    const generatedAt=new Date().toISOString();
    const {analysis,specification,plan}=input;
    const capabilityMatches=input.capabilityMatches??[];
    const base={opportunityId:analysis.opportunityId,specificationId:specification.specificationId,createdAt:generatedAt,approvalState:'draft' as const,externalActionBlocked:true as const};
    const artifact=(type:EngineeringArtifactType,title:string,content:Record<string,unknown>):EngineeringArtifact=>({
      ...base,type,title,content,artifactId:`ENG-${hash({type,content}).slice(0,20)}`,contentHash:hash(content)
    });
    const artifacts:EngineeringArtifact[]=[
      artifact('architecture','System Architecture',{objective:specification.objective,components:specification.components,executionZones:specification.executionZones,missionProblem:analysis.missionProblem}),
      artifact('subsystems','Subsystem Decomposition',{subsystems:specification.components.map((name,index)=>({id:`SUB-${index+1}`,name,requirements:analysis.requirements.filter((_,i)=>i%Math.max(specification.components.length,1)===index).map(r=>r.id)}))}),
      artifact('interfaces','Interface Control Draft',{interfaces:specification.interfaces.map((name,index)=>({id:`IF-${index+1}`,name,ownerZone:specification.executionZones[index%specification.executionZones.length],status:'draft'}))}),
      artifact('risk_register','Risk Register',{risks:analysis.risks.map((risk,index)=>({id:`RISK-${index+1}`,risk,likelihood:'medium',impact:'high',mitigation:'Assign owner and validation evidence.',status:'open'}))}),
      artifact('verification_plan','Verification and Validation Plan',{tests:specification.tests,acceptanceCriteria:specification.acceptanceCriteria,evidenceRequired:specification.evidenceRequired,standards:specification.standards}),
      artifact('simulation_plan','Simulation Plan',{scenarios:plan.tasks.filter(t=>t.kind==='simulation'||t.kind==='design').map(t=>({taskId:t.id,title:t.title,acceptanceCriteria:t.acceptanceCriteria})),fallback:'Create model-based validation for all performance requirements.'}),
      artifact('manufacturing_plan','Manufacturing and Supply Plan',{components:specification.components.map(name=>({name,makeBuyPartner:'undetermined',qualificationRequired:true})),qualityGates:specification.acceptanceCriteria,financialCommitmentsBlocked:true}),
      artifact('documentation_plan','Documentation Plan',{deliverables:analysis.deliverables,taskDocuments:plan.tasks.filter(t=>t.kind==='documentation'||t.kind==='compliance').map(t=>t.title),configurationControl:true}),
      artifact('patent_candidate_package','Patent Candidate Package',{candidateClaims:novelCandidates(analysis,specification,capabilityMatches),priorArtReviewRequired:true,filingBlocked:true,legalReviewRequired:true}),
      artifact('proposal_draft','Proposal Draft Package',{executiveSummary:analysis.missionProblem,technicalApproach:specification.objective,deliverables:analysis.deliverables,evaluationAlignment:analysis.evaluationCriteria,capabilityStrategy:capabilityMatches,submissionBlocked:true})
    ];
    return {programId:`PROGRAM-${hash({analysis,specification,plan}).slice(0,20)}`,opportunityId:analysis.opportunityId,specificationId:specification.specificationId,planId:plan.planId,artifacts,capabilityMatches,generatedAt,externalActionsBlocked:true};
  }
}

function novelCandidates(analysis:TreasuryAnalysis,specification:BuildSpecification,matches:CapabilityMatch[]){
  const buildRequirements=new Set(matches.filter(m=>m.disposition==='build').map(m=>m.requirementId));
  return analysis.requirements.filter(r=>buildRequirements.has(r.id)||r.category==='functional'||r.category==='performance').map(r=>({requirementId:r.id,concept:r.statement,noveltyBasis:`Integration into ${specification.objective}`,status:'candidate'}));
}
function hash(value:unknown){return createHash('sha256').update(JSON.stringify(value)).digest('hex');}
