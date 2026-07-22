import test from 'node:test';
import assert from 'node:assert/strict';
import { EngineeringProgramGenerator } from './engineering-program.js';
import type { BrainPlan, BuildSpecification, TreasuryAnalysis } from './types.js';

test('generates complete draft-only engineering program with external actions blocked',()=>{
  const analysis:TreasuryAnalysis={opportunityId:'OP-1',missionProblem:'Secure autonomous inspection',desiredOutcomes:['validated prototype'],requirements:[{id:'REQ-1',statement:'Detect defects autonomously',category:'functional',mandatory:true,sourceEvidence:'section 3'}],standards:['NIST'],deliverables:['prototype'],evaluationCriteria:['technical merit'],risks:['sensor uncertainty'],fitTags:['robotics'],confidence:.9,reviewRequired:true};
  const specification:BuildSpecification={specificationId:'SPEC-1',opportunityId:'OP-1',objective:'Build inspection system',components:['sensor','planner'],interfaces:['sensor-to-planner'],tests:['defect detection test'],acceptanceCriteria:['95% detection'],standards:['NIST'],evidenceRequired:['test report'],executionZones:['OpenClaw','Nemotron','Hermes','Docker','Manus'],approvalState:'draft'};
  const plan:BrainPlan={planId:'PLAN-1',specificationId:'SPEC-1',tasks:[{id:'T1',title:'Simulate detector',kind:'simulation',dependsOn:[],acceptanceCriteria:['95% detection'],executionZone:'Nemotron'}],externalActionsBlocked:true};
  const program=new EngineeringProgramGenerator().generate({analysis,specification,plan,capabilityMatches:[{requirementId:'REQ-1',score:0,disposition:'build',rationale:'No reusable capability'}]});
  assert.equal(program.artifacts.length,10);
  assert.equal(program.externalActionsBlocked,true);
  assert.ok(program.artifacts.every(a=>a.approvalState==='draft'&&a.externalActionBlocked));
  assert.equal(program.artifacts.find(a=>a.type==='patent_candidate_package')?.content.filingBlocked,true);
  assert.equal(program.artifacts.find(a=>a.type==='proposal_draft')?.content.submissionBlocked,true);
});
