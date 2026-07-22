import test from 'node:test';
import assert from 'node:assert/strict';
import { OpportunityIntakeService } from './intake.js';
import { MemoryOpportunityRepository } from './repository.js';
import { PublicOpportunity } from './types.js';

const base: PublicOpportunity = {
  schemaVersion: '1.0.0',
  eventId: 'sam:ABC-123',
  externalId: 'ABC-123',
  title: 'Resilient Infrastructure Pilot',
  issuer: 'Public Agency',
  jurisdiction: 'US',
  opportunityType: 'RFP',
  publicationDate: '2026-07-21T00:00:00Z',
  deadline: '2026-09-01T21:00:00Z',
  eligibility: ['Small businesses'],
  requiredRegistrations: ['SAM.gov'],
  summary: 'Design and demonstrate a resilient infrastructure platform.',
  provenance: [{ system: 'SAM.gov', authority: 'official', url: 'https://sam.gov/example', retrievedAt: '2026-07-21T12:00:00Z' }]
};

test('deduplicates unchanged records despite retrieval timestamp changes', async () => {
  const service = new OpportunityIntakeService(new MemoryOpportunityRepository());
  const first = await service.ingest({ sourceRunId: 'run-1', receivedAt: '2026-07-21T12:00:00Z', opportunity: base });
  const second = await service.ingest({ sourceRunId: 'run-2', receivedAt: '2026-07-22T12:00:00Z', opportunity: { ...base, provenance: [{ ...base.provenance[0], retrievedAt: '2026-07-22T12:00:00Z' }] } });
  assert.equal(first.result.disposition, 'created');
  assert.equal(second.result.disposition, 'unchanged');
  assert.equal(second.result.stored.revision, 1);
});

test('creates a revision when the deadline changes', async () => {
  const service = new OpportunityIntakeService(new MemoryOpportunityRepository());
  await service.ingest({ sourceRunId: 'run-1', receivedAt: '2026-07-21T12:00:00Z', opportunity: base });
  const amended = await service.ingest({ sourceRunId: 'run-2', receivedAt: '2026-07-22T12:00:00Z', opportunity: { ...base, deadline: '2026-09-15T21:00:00Z', updateDate: '2026-07-22T00:00:00Z' } });
  assert.equal(amended.result.disposition, 'amended');
  assert.equal(amended.result.stored.revision, 2);
  assert.deepEqual(amended.result.changedFields.sort(), ['deadline','updateDate']);
});

test('classifies cancellation notices without authorizing external action', async () => {
  const service = new OpportunityIntakeService(new MemoryOpportunityRepository());
  const receipt = await service.ingest({ sourceRunId: 'run-cancel', receivedAt: '2026-07-22T12:00:00Z', opportunity: { ...base, title: 'Cancelled: Resilient Infrastructure Pilot', summary: 'This opportunity is cancelled.' } });
  assert.equal(receipt.result.disposition, 'cancelled');
  assert.equal(receipt.result.stored.status, 'cancelled');
});
