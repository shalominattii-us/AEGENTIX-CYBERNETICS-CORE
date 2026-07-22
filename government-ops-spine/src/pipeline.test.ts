import test from 'node:test';
import assert from 'node:assert/strict';
import { assertExternalActionAuthorized, runInternalPipeline } from './pipeline.js';
import type { PublicOpportunity } from './types.js';

const fixture: PublicOpportunity = {
  schemaVersion: '1.0.0', eventId: 'event-001', externalId: 'DEMO-001',
  title: 'Resilient Infrastructure Digital Twin', issuer: 'Public Authority', jurisdiction: 'US', opportunityType: 'RFP',
  deadline: '2026-09-30T17:00:00-04:00', eligibility: ['Small businesses'], requiredRegistrations: ['SAM.gov'],
  summary: 'The authority seeks a resilient infrastructure digital twin to improve capital planning.',
  rawText: 'The system shall integrate sensor data using open interfaces. Vendors must demonstrate cybersecurity compliance. The prototype must be validated against an authority-approved test plan. Deliverables include architecture documentation and a working prototype.',
  provenance: [{ system: 'official-portal', authority: 'official', url: 'https://example.gov/opportunity/DEMO-001', retrievedAt: '2026-07-21T12:00:00Z' }]
};

test('creates an internal build plan while blocking external actions', () => {
  const result = runInternalPipeline(fixture, [{ id: 'AX-CAP-DIGITAL-TWIN', name: 'AEGENTIX Digital Twin Core', tags: ['digital','twin','sensor','data','interfaces'], maturity: 'TRL-5', evidence: ['repo://AEGENTIX-CYBERNETICS-CORE'], executionZones: ['OpenClaw','Nemotron','Hermes','Docker','Manus'] }]);
  assert.ok(result.analysis.requirements.length >= 3);
  assert.equal(result.specification.approvalState, 'draft');
  assert.equal(result.plan.externalActionsBlocked, true);
  assert.throws(() => assertExternalActionAuthorized('submit_offer'));
  assert.doesNotThrow(() => assertExternalActionAuthorized('submit_offer', 'AEGENTIX-AUTH-review-token'));
});
