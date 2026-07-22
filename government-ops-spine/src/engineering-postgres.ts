import type { Pool } from 'pg';
import type { BrainPlan, BuildSpecification, CapabilityMatch, TreasuryAnalysis } from './types.js';
import { EngineeringProgramGenerator, type EngineeringProgram } from './engineering-program.js';

export class PostgresEngineeringProgramService {
  private readonly generator=new EngineeringProgramGenerator();
  constructor(private readonly pool:Pool){}

  async generateForOpportunity(opportunityId:string):Promise<EngineeringProgram>{
    const [analysisResult,specResult,planResult,matchesResult]=await Promise.all([
      this.pool.query('select analysis_json from treasury_analyses where opportunity_id=$1',[opportunityId]),
      this.pool.query('select specification_json from build_specifications where opportunity_id=$1 order by updated_at desc limit 1',[opportunityId]),
      this.pool.query(`select bp.plan_json from brain_plans bp join build_specifications bs on bs.specification_id=bp.specification_id where bs.opportunity_id=$1 order by bp.updated_at desc limit 1`,[opportunityId]),
      this.pool.query('select requirement_id,capability_id,score,disposition,rationale from capability_matches where opportunity_id=$1 order by requirement_id',[opportunityId])
    ]);
    if(!analysisResult.rowCount||!specResult.rowCount||!planResult.rowCount) throw new Error('Analysis, specification, and brain plan are required before engineering-program generation.');
    const analysis=analysisResult.rows[0].analysis_json as TreasuryAnalysis;
    const specification=specResult.rows[0].specification_json as BuildSpecification;
    const plan=planResult.rows[0].plan_json as BrainPlan;
    const capabilityMatches=matchesResult.rows.map(row=>({requirementId:row.requirement_id,capabilityId:row.capability_id??undefined,score:Number(row.score),disposition:row.disposition,rationale:row.rationale})) as CapabilityMatch[];
    const program=this.generator.generate({analysis,specification,plan,capabilityMatches});
    await this.save(program);
    await this.pool.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values('engineering.program.generated',$1,$2)`,[opportunityId,{programId:program.programId,artifactCount:program.artifacts.length,externalActionsBlocked:true}]);
    return program;
  }

  async get(programId:string):Promise<EngineeringProgram|undefined>{
    const programResult=await this.pool.query('select * from engineering_programs where program_id=$1',[programId]);
    if(!programResult.rowCount)return undefined;
    const artifactResult=await this.pool.query('select * from engineering_artifacts where program_id=$1 order by artifact_type',[programId]);
    const row=programResult.rows[0];
    return {programId:row.program_id,opportunityId:row.opportunity_id,specificationId:row.specification_id,planId:row.plan_id,capabilityMatches:row.capability_matches_json,generatedAt:new Date(row.generated_at).toISOString(),externalActionsBlocked:true,artifacts:artifactResult.rows.map(a=>({artifactId:a.artifact_id,opportunityId:a.opportunity_id,specificationId:a.specification_id,type:a.artifact_type,title:a.title,content:a.content_json,contentHash:a.content_hash,createdAt:new Date(a.created_at).toISOString(),approvalState:a.approval_state,externalActionBlocked:true}))};
  }

  async listByOpportunity(opportunityId:string):Promise<Array<{programId:string;generatedAt:string;artifactCount:number}>>{
    const result=await this.pool.query(`select p.program_id,p.generated_at,count(a.artifact_id)::int artifact_count from engineering_programs p left join engineering_artifacts a on a.program_id=p.program_id where p.opportunity_id=$1 group by p.program_id,p.generated_at order by p.generated_at desc`,[opportunityId]);
    return result.rows.map(r=>({programId:r.program_id,generatedAt:new Date(r.generated_at).toISOString(),artifactCount:r.artifact_count}));
  }

  private async save(program:EngineeringProgram):Promise<void>{
    const client=await this.pool.connect();
    try{
      await client.query('begin');
      await client.query(`insert into engineering_programs(program_id,opportunity_id,specification_id,plan_id,capability_matches_json,generated_at,external_actions_blocked) values($1,$2,$3,$4,$5,$6,true) on conflict(program_id) do update set capability_matches_json=excluded.capability_matches_json,generated_at=excluded.generated_at`,[program.programId,program.opportunityId,program.specificationId,program.planId,program.capabilityMatches,program.generatedAt]);
      for(const a of program.artifacts) await client.query(`insert into engineering_artifacts(artifact_id,program_id,opportunity_id,specification_id,artifact_type,title,content_json,content_hash,approval_state,external_action_blocked,created_at) values($1,$2,$3,$4,$5,$6,$7,$8,$9,true,$10) on conflict(artifact_id) do update set content_json=excluded.content_json,content_hash=excluded.content_hash,title=excluded.title`,[a.artifactId,program.programId,a.opportunityId,a.specificationId,a.type,a.title,a.content,a.contentHash,a.approvalState,a.createdAt]);
      await client.query('commit');
    }catch(error){await client.query('rollback');throw error;}finally{client.release();}
  }
}
