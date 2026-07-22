import test from 'node:test';
import assert from 'node:assert/strict';
import { CapabilityIndexer, MemoryCapabilityRegistry, StaticCapabilitySource, dockerAsset, documentAsset, githubAsset } from './capability-indexer.js';
import { createBrainPlan, generateBuildSpecification } from './pipeline.js';
import type { TreasuryAnalysis } from './types.js';

test('indexes assets and feeds matches into the brain plan',async()=>{
 const registry=new MemoryCapabilityRegistry();
 const source=new StaticCapabilitySource('fixture',[
  githubAsset({fullName:'aegentix/cyber-agent',description:'cybersecurity agent API and automation',topics:['cybersecurity','agent','api'],language:'TypeScript',url:'https://github.com/aegentix/cyber-agent'}),
  dockerAsset({image:'aegentix/cyber-agent:latest',container:'cyber-agent',status:'running',ports:['8080:8080']}),
  documentAsset({path:'docs/cyber-agent.md',title:'Cyber Agent Validation',text:'Validated cybersecurity automation agent with API integration and test evidence.'})
 ]);
 const indexer=new CapabilityIndexer(registry,[source]);
 const result=await indexer.run();
 assert.equal(result.scanned,3);
 const analysis:TreasuryAnalysis={opportunityId:'OPP-1',missionProblem:'Provide cybersecurity agent API automation',desiredOutcomes:[],requirements:[{id:'REQ-1',statement:'The system shall provide cybersecurity agent API automation',category:'functional',mandatory:true,sourceEvidence:'source'}],standards:[],deliverables:[],evaluationCriteria:[],risks:[],fitTags:['cybersecurity','agent','api','automation'],confidence:.9,reviewRequired:false};
 const specification=generateBuildSpecification(analysis);
 const planned=await indexer.planWithCapabilities('OPP-1',analysis,createBrainPlan(specification));
 assert.equal(planned.matches.length,1);
 assert.notEqual(planned.matches[0].disposition,'build');
 assert.equal(planned.plan.capabilityMatches.length,1);
});
