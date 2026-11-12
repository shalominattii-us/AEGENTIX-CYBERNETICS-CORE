import { hashOpportunity, normalizeOpportunity } from '../intake.js';
export async function persistOpportunity(db, input) {
    const opportunity = normalizeOpportunity(input.opportunity);
    const canonicalHash = hashOpportunity(opportunity);
    const sourceSystem = opportunity.provenance[0]?.system ?? 'unknown';
    const existing = await db.prepare(`select event_id, canonical_hash, revision, status, opportunity_json from opportunity_records where source_system = ? and external_id = ?`).bind(sourceSystem, opportunity.externalId).first();
    if (existing?.canonical_hash === canonicalHash) {
        await db.prepare(`update opportunity_records set last_seen_at = ? where event_id = ?`).bind(input.receivedAt, existing.event_id).run();
        return { eventId: existing.event_id, externalId: opportunity.externalId, disposition: 'unchanged', canonicalHash, revision: existing.revision };
    }
    const revision = (existing?.revision ?? 0) + 1;
    const status = inferStatus(opportunity);
    const disposition = status === 'cancelled' ? 'cancelled' : status === 'awarded' ? 'awarded' : existing ? 'amended' : 'created';
    const changedFields = existing ? diffStored(existing, opportunity) : [];
    const opportunityJson = JSON.stringify(opportunity);
    const payload = JSON.stringify({ sourceRunId: input.sourceRunId, receivedAt: input.receivedAt, opportunity });
    await db.batch([
        db.prepare(`insert into opportunity_records (event_id, external_id, source_system, canonical_hash, revision, status, opportunity_json, first_seen_at, last_seen_at)
       values (?, ?, ?, ?, ?, ?, ?, ?, ?)
       on conflict(source_system, external_id) do update set
         event_id = excluded.event_id,
         canonical_hash = excluded.canonical_hash,
         revision = excluded.revision,
         status = excluded.status,
         opportunity_json = excluded.opportunity_json,
         last_seen_at = excluded.last_seen_at`).bind(opportunity.eventId, opportunity.externalId, sourceSystem, canonicalHash, revision, status, opportunityJson, input.receivedAt, input.receivedAt),
        db.prepare(`insert into opportunity_revisions (event_id, revision, canonical_hash, change_type, changed_fields, opportunity_json, observed_at)
       values (?, ?, ?, ?, ?, ?, ?)`).bind(opportunity.eventId, revision, canonicalHash, disposition, JSON.stringify(changedFields), opportunityJson, input.receivedAt),
        db.prepare(`insert into intake_outbox (event_type, aggregate_id, payload_json, occurred_at) values (?, ?, ?, ?)`).bind(`opportunity.${disposition}`, opportunity.eventId, payload, input.receivedAt)
    ]);
    return { eventId: opportunity.eventId, externalId: opportunity.externalId, disposition, canonicalHash, revision };
}
function inferStatus(opportunity) {
    const text = `${opportunity.title} ${opportunity.summary}`.toLowerCase();
    if (text.includes('cancelled') || text.includes('canceled'))
        return 'cancelled';
    if (text.includes('award notice') || text.includes('awarded'))
        return 'awarded';
    if (opportunity.deadline && Date.parse(opportunity.deadline) < Date.now())
        return 'closed';
    return 'active';
}
function diffStored(before, after) {
    let previous;
    try {
        previous = JSON.parse(before.opportunity_json);
    }
    catch {
        return [];
    }
    return Object.keys(after).filter((key) => JSON.stringify(previous[key]) !== JSON.stringify(after[key])).map(String);
}
