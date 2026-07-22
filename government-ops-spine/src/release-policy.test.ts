import test from 'node:test';
import assert from 'node:assert/strict';
import type { EngineeringArtifact } from './engineering-program.js';
import { evaluateReleasePolicy, requiredRolesFor } from './release-policy.js';

const artifact:EngineeringArtifact={
  artifactId:'ENG-PATENT-1',
  opportunityId:'OPP-1',
  specificationId:'SPEC-1',
  type:'patent_candidate_package',
  title:'Patent Candidate Package',
  content:{candidateClaims:[]},
  contentHash:'hash-current',
  createdAt:'2026-07-22T00:00:00.000Z',
  approvalState:'draft',
  externalActionBlocked:true
};

test('patent package requires technical, legal, and executive approvals on the current hash',()=>{
  assert.deepEqual(requiredRolesFor('patent_candidate_package'),['technical','legal','executive']);
  const partial=evaluateReleasePolicy(artifact,[
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'technical',reviewerId:'REV-T',decision:'approve',reviewedAt:'2026-07-22T01:00:00.000Z'},
    {artifactId:artifact.artifactId,artifactHash:'stale-hash',reviewerRole:'legal',reviewerId:'REV-L',decision:'approve',reviewedAt:'2026-07-22T01:05:00.000Z'}
  ]);
  assert.equal(partial.releaseState,'internal_review');
  assert.deepEqual(partial.missingRoles,['legal','executive']);
  assert.equal(partial.externalActionBlocked,true);

  const complete=evaluateReleasePolicy(artifact,[
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'technical',reviewerId:'REV-T',decision:'approve',reviewedAt:'2026-07-22T01:00:00.000Z'},
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'legal',reviewerId:'REV-L',decision:'approve',reviewedAt:'2026-07-22T01:05:00.000Z'},
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'executive',reviewerId:'REV-E',decision:'approve',reviewedAt:'2026-07-22T01:10:00.000Z'}
  ]);
  assert.equal(complete.releaseState,'role_review_complete');
  assert.deepEqual(complete.missingRoles,[]);
  assert.equal(complete.externalActionBlocked,true);
});

test('a later request-changes decision blocks release',()=>{
  const result=evaluateReleasePolicy(artifact,[
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'technical',reviewerId:'REV-T',decision:'approve',reviewedAt:'2026-07-22T01:00:00.000Z'},
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'legal',reviewerId:'REV-L',decision:'approve',reviewedAt:'2026-07-22T01:05:00.000Z'},
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'legal',reviewerId:'REV-L',decision:'request_changes',reviewedAt:'2026-07-22T01:06:00.000Z'},
    {artifactId:artifact.artifactId,artifactHash:'hash-current',reviewerRole:'executive',reviewerId:'REV-E',decision:'approve',reviewedAt:'2026-07-22T01:10:00.000Z'}
  ]);
  assert.equal(result.releaseState,'internal_review');
  assert.deepEqual(result.missingRoles,['legal']);
  assert.equal(result.blockingDecisions.length,1);
});
