import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { OpportunityIntakeService } from './intake.js';
import { MemoryOpportunityRepository } from './repository.js';
import { GovernmentOpsRuntime } from './runtime.js';
import { assertExternalActionAuthorized, parseOpportunity } from './pipeline.js';
import { searchSamGov } from './sam-gov.js';
import { loadFoundryInput, opportunityFromFoundry, runFoundryIngest, runtimeSink } from './foundry-bridge.js';
import { runFoundryIngestCli } from './foundry-ingest-cli.js';
import { FoundryIngestScheduler, startEmbeddedFoundryIngest } from './foundry-ingest-worker.js';

const fixtureRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../fixtures/foundry/workspace');
const runDir = path.join(fixtureRoot, 'runs', '20260721T120000000000Z');
const reportPath = path.join(fixtureRoot, 'latest-report.json');
const dispositions = ['HUMAN_REVIEW'];
const naics = ['541512', '541715'];
const apiKey = 'unit-test-sam-key';

function harness() {
  const repository = new MemoryOpportunityRepository();
  const runtime = new GovernmentOpsRuntime(repository);
  return { repository, sink: runtimeSink(runtime) };
}

const rawNotice = {
  noticeId: 'NOTICE-API-541512',
  title: 'Direct API software solicitation',
  type: 'Solicitation',
  naicsCode: '541512',
  fullParentPathName: 'GENERAL SERVICES ADMINISTRATION.FAS',
  uiLink: 'https://sam.gov/opp/NOTICE-API-541512/view',
  description: 'The contractor shall deliver software for the agency.',
  responseDeadLine: '2099-04-01T12:00:00Z',
  postedDate: '2026-07-21',
  resourceLinks: ['https://sam.gov/files/b.pdf', 'https://sam.gov/files/a.pdf']
};

test('external action authorization stays blocked', () => {
  assert.throws(() => assertExternalActionAuthorized('submit_offer'), /blocked/);
  assert.throws(() => assertExternalActionAuthorized('external_representation'), /blocked/);
  assert.throws(() => assertExternalActionAuthorized('file_patent'), /blocked/);
  assert.throws(() => assertExternalActionAuthorized('commit_funds'), /blocked/);
});

test('loads the latest Foundry run and maps official SAM.gov provenance', async () => {
  const batch = await loadFoundryInput(fixtureRoot);
  assert.equal(batch.sourceRunId, '20260721T120000000000Z');
  assert.equal(batch.records.some((record) => record.externalId === 'OLD-NOTICE-541512'), false);
  const { repository, sink } = harness();
  const first = await runFoundryIngest(sink, { path: runDir, dispositions, naics, receivedAt: '2026-07-21T12:00:00Z' });
  assert.deepEqual(first.selectedExternalIds, ['NOTICE-HUMAN-541512', 'PARTNER-1']);
  assert.equal(first.results.every((result) => result.disposition === 'created'), true);
  const reasons = Object.fromEntries(first.skipped.map((skip) => [skip.externalId, skip.reason]));
  assert.equal(reasons['NOTICE-FORECAST-541715'], 'disposition');
  assert.equal(reasons['NOTICE-CLOSED-541512'], 'disposition');
  assert.equal(reasons['NOTICE-HUMAN-541330'], 'naics');

  const stored = await repository.getByEventId('sam:NOTICE-HUMAN-541512');
  assert.ok(stored);
  const opportunity = stored.opportunity;
  assert.equal(opportunity.externalId, 'NOTICE-HUMAN-541512');
  assert.equal(opportunity.issuer, 'DEPARTMENT OF DEFENSE.DEPT OF THE NAVY.NAVAL RESEARCH LAB');
  assert.equal(opportunity.jurisdiction, 'United States');
  assert.equal(opportunity.opportunityType, 'RFP');
  assert.equal(opportunity.publicationDate, '2026-07-21');
  assert.equal(opportunity.deadline, '2099-01-01T17:00:00-05:00');
  assert.equal(opportunity.setAside, 'Total Small Business Set-Aside (FAR 19.5)');
  assert.equal(opportunity.location, 'Washington, DC, 20375, USA');
  assert.equal(opportunity.submissionMethod, 'SAM.gov');
  assert.ok(opportunity.requiredRegistrations.includes('SAM.gov'));
  assert.match(opportunity.summary, /shall deliver a cybersecurity software prototype/);
  assert.match(opportunity.rawText ?? '', /PSC: D307/);
  assert.match(opportunity.rawText ?? '', /NAICS: 541512/);
  assert.match(opportunity.rawText ?? '', /Alex Example/);
  assert.match(opportunity.rawText ?? '', /N00173-27-R-0001/);
  assert.equal(opportunity.provenance[0]?.system, 'SAM.gov');
  assert.equal(opportunity.provenance[0]?.authority, 'official');
  assert.equal(opportunity.provenance[0]?.url, 'https://sam.gov/opp/NOTICE-HUMAN-541512/view');
  assert.deepEqual(opportunity.provenance[0]?.attachmentUrls, ['https://sam.gov/files/statement.pdf']);
  const analysis = parseOpportunity(opportunity);
  assert.equal(analysis.reviewRequired, false);
  assert.equal(analysis.risks.includes('Non-official provenance requires verification.'), false);

  const partner = await repository.getByEventId('state-procurement-bulletin:PARTNER-1');
  assert.ok(partner);
  assert.equal(partner.opportunity.provenance[0]?.system, 'State procurement bulletin');
  assert.equal(partner.opportunity.provenance[0]?.authority, 'aggregator');
  assert.equal(partner.opportunity.provenance[0]?.url, 'https://example.gov/notices/PARTNER-1');
  assert.equal(partner.opportunity.requiredRegistrations.includes('SAM.gov'), false);
  const partnerAnalysis = parseOpportunity(partner.opportunity);
  assert.equal(partnerAnalysis.reviewRequired, true);
  assert.ok(partnerAnalysis.risks.includes('Non-official provenance requires verification.'));

  const second = await runFoundryIngest(sink, { path: runDir, dispositions, naics, receivedAt: '2026-07-22T00:00:00Z' });
  assert.equal(second.results.every((result) => result.disposition === 'unchanged'), true);
  const human = second.results.find((result) => result.externalId === 'NOTICE-HUMAN-541512');
  assert.equal(human?.revision, 1);
  assert.equal(human?.canonicalHash, first.results.find((result) => result.externalId === 'NOTICE-HUMAN-541512')?.canonicalHash);
});

test('disposition and NAICS filters are configurable', async () => {
  const forecast = harness();
  const selectedForecast = await runFoundryIngest(forecast.sink, { path: runDir, dispositions: ['FORECAST_MONITOR'], naics, dryRun: false });
  assert.deepEqual(selectedForecast.selectedExternalIds, ['NOTICE-FORECAST-541715']);
  const stored = await forecast.repository.getByEventId('sam:NOTICE-FORECAST-541715');
  assert.equal(stored?.opportunity.opportunityType, 'FORECAST');

  const byDisposition = harness();
  const humanDisposition = await runFoundryIngest(byDisposition.sink, { path: runDir, dispositions: ['REQUIRES_HUMAN_DECISION'], naics, dryRun: true });
  assert.deepEqual(humanDisposition.selectedExternalIds, ['NOTICE-HUMAN-541512', 'PARTNER-1']);
  assert.equal(humanDisposition.results.length, 0);
  assert.equal(await byDisposition.repository.getByEventId('sam:NOTICE-HUMAN-541512'), undefined);

  const narrowed = harness();
  const onlyFacilities = await runFoundryIngest(narrowed.sink, { path: runDir, dispositions, naics: ['541330'], dryRun: true });
  assert.deepEqual(onlyFacilities.selectedExternalIds, ['NOTICE-HUMAN-541330']);
});

test('latest-report.json keeps scored records and skips unscored ones by default', async () => {
  const { sink } = harness();
  const filtered = await runFoundryIngest(sink, { path: reportPath, dispositions, naics, dryRun: true });
  assert.deepEqual(filtered.selectedExternalIds, ['NOTICE-REPORT-SCORED']);
  assert.equal(filtered.skipped.find((skip) => skip.externalId === 'NOTICE-REPORT-541512')?.reason, 'disposition_missing');
  assert.equal(filtered.skipped.find((skip) => skip.externalId === 'NOTICE-REPORT-FORECAST')?.reason, 'disposition');
  const open = await runFoundryIngest(sink, { path: reportPath, dispositions: [], naics, dryRun: true });
  assert.deepEqual(open.selectedExternalIds, ['NOTICE-REPORT-541512', 'NOTICE-REPORT-FORECAST', 'NOTICE-REPORT-SCORED']);
});

test('re-ingesting the same noticeId is unchanged when only the retrieval time differs', async () => {
  const repository = new MemoryOpportunityRepository();
  const intake = new OpportunityIntakeService(repository);
  const earlier = opportunityFromFoundry(rawNotice, { origin: 'sam-api', retrievedAt: '2026-07-21T00:00:00Z' });
  const later = opportunityFromFoundry(rawNotice, { origin: 'sam-api', retrievedAt: '2026-08-01T00:00:00Z' });
  const reversed = opportunityFromFoundry({ ...rawNotice, resourceLinks: ['https://sam.gov/files/a.pdf', 'https://sam.gov/files/b.pdf'] }, { origin: 'sam-api', retrievedAt: '2026-07-21T00:00:00Z' });
  assert.notEqual(earlier.opportunity.provenance[0]?.retrievedAt, later.opportunity.provenance[0]?.retrievedAt);
  assert.deepEqual(earlier.opportunity.provenance[0]?.attachmentUrls, reversed.opportunity.provenance[0]?.attachmentUrls);
  const first = await intake.ingest({ sourceRunId: 'sam-1', receivedAt: '2026-07-21T00:00:00Z', opportunity: earlier.opportunity });
  const second = await intake.ingest({ sourceRunId: 'sam-2', receivedAt: '2026-08-01T00:00:00Z', opportunity: later.opportunity });
  const sameAttachments = await intake.ingest({ sourceRunId: 'sam-3', receivedAt: '2026-08-01T00:00:00Z', opportunity: reversed.opportunity });
  assert.equal(first.result.disposition, 'created');
  assert.equal(second.result.disposition, 'unchanged');
  assert.equal(sameAttachments.result.disposition, 'unchanged');
  assert.equal(first.canonicalHash, second.canonicalHash);
  const amended = opportunityFromFoundry({ ...rawNotice, responseDeadLine: '2099-05-01T12:00:00Z' }, { origin: 'sam-api', retrievedAt: '2026-08-02T00:00:00Z' });
  const third = await intake.ingest({ sourceRunId: 'sam-4', receivedAt: '2026-08-02T00:00:00Z', opportunity: amended.opportunity });
  assert.equal(third.result.disposition, 'amended');
  assert.equal(third.result.stored.revision, 2);
  assert.ok(third.result.changedFields.includes('deadline'));
});

test('direct SAM.gov pull uses official provenance, NAICS filters, and redacts the key', async () => {
  const urls: URL[] = [];
  const fetchImpl: typeof fetch = async (input) => {
    const url = new URL(String(input));
    urls.push(url);
    if (url.searchParams.get('ncode') === '541512') {
      return Response.json({ totalRecords: 1, opportunitiesData: [rawNotice, { ...rawNotice, noticeId: 'NOTICE-API-OTHER', naicsCode: '541330', title: 'Unrelated facilities notice', uiLink: 'https://sam.gov/opp/NOTICE-API-OTHER/view' }] });
    }
    return Response.json({ totalRecords: 0, opportunitiesData: [] });
  };
  const { repository, sink } = harness();
  const summary = await runFoundryIngest(sink, {
    dispositions,
    naics,
    secrets: [apiKey],
    pull: { apiKey, now: () => new Date('2026-07-22T15:00:00.000Z'), fetchImpl, naics, lookbackDays: 1, limit: 10 }
  });
  assert.deepEqual(summary.selectedExternalIds, ['NOTICE-API-541512']);
  assert.equal(summary.results[0]?.disposition, 'created');
  assert.equal(JSON.stringify(summary).includes(apiKey), false);
  assert.equal(summary.skipped.find((skip) => skip.externalId === 'NOTICE-API-OTHER')?.reason, 'naics');
  assert.ok(urls.every((url) => url.hostname === 'api.sam.gov' && url.pathname === '/opportunities/v2/search'));
  assert.deepEqual(urls.map((url) => url.searchParams.get('ncode')).sort(), ['541512', '541715']);
  assert.equal(urls[0]?.searchParams.get('postedFrom'), '07/21/2026');
  assert.equal(urls[0]?.searchParams.get('postedTo'), '07/22/2026');
  const stored = await repository.getByEventId('sam:NOTICE-API-541512');
  assert.equal(stored?.opportunity.provenance[0]?.authority, 'official');
  assert.equal(stored?.opportunity.provenance[0]?.system, 'SAM.gov');
  assert.equal(stored?.opportunity.submissionMethod, 'SAM.gov');
  const repeat = await runFoundryIngest(sink, {
    dispositions,
    naics,
    secrets: [apiKey],
    pull: { apiKey, now: () => new Date('2026-08-01T00:00:00.000Z'), fetchImpl, naics, postedFrom: '07/21/2026', postedTo: '07/22/2026', limit: 10 }
  });
  assert.equal(repeat.results[0]?.disposition, 'unchanged');
  assert.equal(repeat.results[0]?.canonicalHash, summary.results[0]?.canonicalHash);
});

test('SAM.gov client pages results, refuses other hosts, and never returns the key', async () => {
  const seen: string[] = [];
  const notices = await searchSamGov({
    apiKey,
    postedFrom: '07/21/2026',
    postedTo: '07/22/2026',
    limit: 1,
    naics: '541512',
    fetchImpl: async (input) => {
      const url = String(input);
      seen.push(url);
      const offset = new URL(url).searchParams.get('offset');
      if (offset === '0') return Response.json({ totalRecords: 2, opportunitiesData: [{ noticeId: 'ONE', title: 'One' }] });
      return Response.json({ totalRecords: 2, opportunitiesData: [{ noticeId: 'TWO', title: 'Two' }] });
    }
  });
  assert.deepEqual(notices.map((notice) => notice.noticeId), ['ONE', 'TWO']);
  assert.equal(seen.length, 2);
  assert.equal(JSON.stringify(notices).includes(apiKey), false);

  let called = false;
  await assert.rejects(
    () => searchSamGov({ apiKey, postedFrom: '07/21/2026', postedTo: '07/22/2026', endpoint: 'https://evil.example/search', fetchImpl: async () => { called = true; return Response.json({}); } }),
    /api\.sam\.gov/
  );
  assert.equal(called, false);

  await assert.rejects(
    () => searchSamGov({
      apiKey,
      postedFrom: '07/21/2026',
      postedTo: '07/22/2026',
      fetchImpl: async (input) => { throw new Error(`connect failed for ${String(input)}`); }
    }),
    (error: unknown) => {
      const message = error instanceof Error ? error.message : String(error);
      assert.match(message, /SAM.gov request failed/);
      assert.equal(message.includes(apiKey), false);
      assert.match(message, /api_key=\[redacted\]/);
      return true;
    }
  );

  await assert.rejects(
    () => searchSamGov({
      apiKey,
      postedFrom: '07/21/2026',
      postedTo: '07/22/2026',
      fetchImpl: async () => new Response(JSON.stringify({ message: `rejected ${apiKey}` }), { status: 401 })
    }),
    (error: unknown) => {
      const message = error instanceof Error ? error.message : String(error);
      assert.match(message, /HTTP 401/);
      assert.equal(message.includes(apiKey), false);
      return true;
    }
  );

  let redirects = 0;
  await assert.rejects(
    () => searchSamGov({
      apiKey,
      postedFrom: '07/21/2026',
      postedTo: '07/22/2026',
      fetchImpl: async () => {
        redirects += 1;
        return new Response(null, { status: 302, headers: { location: `https://evil.example/?api_key=${apiKey}` } });
      }
    }),
    (error: unknown) => {
      const message = error instanceof Error ? error.message : String(error);
      assert.match(message, /redirect was not followed/);
      assert.equal(message.includes(apiKey), false);
      assert.equal(redirects, 1);
      return true;
    }
  );
});

test('award notices stay official and are classified as awarded', async () => {
  const repository = new MemoryOpportunityRepository();
  const intake = new OpportunityIntakeService(repository);
  const award = opportunityFromFoundry({
    noticeId: 'AWARD-1',
    title: 'Platform support',
    type: 'Award Notice',
    naicsCode: '541512',
    fullParentPathName: 'DEPARTMENT OF DEFENSE',
    uiLink: 'https://sam.gov/opp/AWARD-1/view',
    active: 'Yes'
  }, { origin: 'sam-api', retrievedAt: '2026-07-21T00:00:00Z' });
  assert.equal(award.opportunity.provenance[0]?.authority, 'official');
  const receipt = await intake.ingest({ sourceRunId: 'award', receivedAt: '2026-07-21T00:00:00Z', opportunity: award.opportunity });
  assert.equal(receipt.result.disposition, 'awarded');
  assert.equal(receipt.result.stored.status, 'awarded');
});

test('malicious opportunity ids do not escape the run directory', async () => {
  const directory = await mkdtemp(path.join(tmpdir(), 'foundry-bridge-'));
  try {
    await mkdir(path.join(directory, 'opportunities'), { recursive: true });
    await mkdir(path.join(directory, 'intelligence'), { recursive: true });
    await writeFile(path.join(directory, 'secret.json'), JSON.stringify({ leaked: true }));
    await writeFile(path.join(directory, 'opportunities', 'bad.json'), JSON.stringify({
      opportunity_id: '../secret',
      title: 'Escaping notice',
      source: 'SAM.gov',
      external_id: 'BAD-1',
      jurisdiction: 'United States',
      opportunity_type: 'Solicitation',
      provenance: { source_name: 'SAM.gov', source_url: 'https://sam.gov/opp/BAD-1/view', source_record_id: 'BAD-1', retrieved_at: '2026-07-21T00:00:00Z' },
      issuer: 'DEPARTMENT OF DEFENSE',
      sectors: ['541512'],
      metadata: { naics: ['541512'], description: 'The contractor shall stay inside the run directory.' }
    }));
    const batch = await loadFoundryInput(directory);
    assert.equal(batch.records.length, 1);
    assert.equal(batch.records[0]?.intelligence, undefined);
    assert.equal(JSON.stringify(batch).includes('leaked'), false);
    assert.equal(batch.errors.length, 0);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('CLI ingests a Foundry path and a direct pull without printing the key', async () => {
  const { sink } = harness();
  const logs: string[] = [];
  const fileCode = await runFoundryIngestCli([runDir, '--dry-run'], {
    env: {},
    sink,
    stdout: (line) => logs.push(line),
    stderr: (line) => logs.push(line)
  });
  assert.equal(fileCode, 0);
  const fileSummary = JSON.parse(logs.at(-1) ?? '{}') as { selectedExternalIds: string[] };
  assert.deepEqual(fileSummary.selectedExternalIds, ['NOTICE-HUMAN-541512', 'PARTNER-1']);

  const pullLogs: string[] = [];
  const pullErrors: string[] = [];
  const pullCode = await runFoundryIngestCli(['--pull', '--naics', '541512', '--posted-from', '07/21/2026', '--posted-to', '07/22/2026'], {
    env: { SAM_GOV_API_KEY: apiKey },
    sink,
    now: () => new Date('2026-07-22T15:00:00.000Z'),
    fetchImpl: async () => Response.json({ totalRecords: 1, opportunitiesData: [rawNotice] }),
    stdout: (line) => pullLogs.push(line),
    stderr: (line) => pullErrors.push(line)
  });
  assert.equal(pullCode, 0, pullErrors.join('\n'));
  assert.equal(pullLogs.join('\n').includes(apiKey), false);
  const pullSummary = JSON.parse(pullLogs.at(-1) ?? '{}') as { results: Array<{ disposition: string; externalId: string }> };
  assert.equal(pullSummary.results[0]?.externalId, 'NOTICE-API-541512');
  assert.equal(pullSummary.results[0]?.disposition, 'created');

  const missing: string[] = [];
  const missingCode = await runFoundryIngestCli(['--pull'], { env: {}, sink, stderr: (line) => missing.push(line) });
  assert.equal(missingCode, 2);
  assert.match(missing.join('\n'), /SAM_GOV_API_KEY is required/);
  assert.equal(missing.join('\n').includes(apiKey), false);
});

test('scheduler runs one ingest at a time and can be disabled', async () => {
  assert.equal(startEmbeddedFoundryIngest(new MemoryOpportunityRepository(), {}), undefined);
  assert.equal(startEmbeddedFoundryIngest(new MemoryOpportunityRepository(), { FOUNDRY_INGEST_ENABLED: 'true' }), undefined);
  let active = 0;
  let maxActive = 0;
  let release = () => {};
  const gate = new Promise<void>((resolve) => { release = resolve; });
  const scheduler = new FoundryIngestScheduler(60_000, async () => {
    active += 1;
    maxActive = Math.max(maxActive, active);
    await gate;
    active -= 1;
  });
  const first = scheduler.runOnce();
  const second = scheduler.runOnce();
  release();
  await first;
  await second;
  assert.equal(maxActive, 1);
  scheduler.stop();

  const repository = new MemoryOpportunityRepository();
  const embedded = startEmbeddedFoundryIngest(repository, {
    FOUNDRY_INGEST_ENABLED: 'true',
    FOUNDRY_INGEST_PATH: runDir,
    FOUNDRY_INGEST_INTERVAL_MS: '60000',
    FOUNDRY_INGEST_NAICS: '541512,541715',
    FOUNDRY_INGEST_DISPOSITIONS: 'HUMAN_REVIEW'
  });
  assert.ok(embedded);
  await embedded.whenSettled();
  embedded.stop();
  const stored = await repository.getByEventId('sam:NOTICE-HUMAN-541512');
  assert.equal(stored?.opportunity.provenance[0]?.authority, 'official');
});

test('CLI warns before posting to the local spine when no database or endpoint is configured', async () => {
  const errors: string[] = [];
  const code = await runFoundryIngestCli([runDir, '--dry-run'], {
    env: {},
    stdout: () => {},
    stderr: (line) => errors.push(line)
  });
  assert.equal(code, 0);
  assert.match(errors.join('\n'), /http:\/\/127\.0\.0\.1:8099\/api\/opportunities\/ingest/);
});
