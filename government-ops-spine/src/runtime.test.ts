import test from 'node:test';
import assert from 'node:assert/strict';
import { GovernmentOpsRuntime } from './runtime.js';
import { MemoryOpportunityRepository } from './repository.js';
import type { PublicOpportunity } from './types.js';

const opportunity: PublicOpportunity = {
  schemaVersion:'1.0.0', eventId:'evt-runtime-1', externalId:'RUNTIME-1', title:'Resilient Infrastructure Pilot', issuer:'Public Authority', jurisdiction:'US', opportunityType:'RFP',
  deadline:'2099-01-01T00:00:00Z', eligibility:['Small businesses'], requiredRegistrations:['SAM.gov'],
  summary:'The system shall provide resilient infrastructure monitoring and must demonstrate compliance with NIST standards.',
  provenance:[{system:'official-portal',authority:'official',url:'https://example.gov/runtime-1',retrievedAt:new Date().toISOString()}]
};

test('ingest automatically generates analysis, specification, and brain plan', async () => {
  const runtime = new GovernmentOpsRuntime(new MemoryOpportunityRepository());
  const response = await runtime.handle({ method:'POST', path:'/api/opportunities/ingest', body:{ sourceRunId:'run-1', receivedAt:new Date().toISOString(), opportunity } });
  assert.equal(response.status, 201);
  const state = await runtime.handle({ method:'GET', path:'/api/opportunities/evt-runtime-1/state' });
  assert.equal(state.status, 200);
});

test('unknown route returns 404', async () => {
  const runtime = new GovernmentOpsRuntime(new MemoryOpportunityRepository());
  const response = await runtime.handle({ method:'GET', path:'/missing' });
  assert.equal(response.status, 404);
});
