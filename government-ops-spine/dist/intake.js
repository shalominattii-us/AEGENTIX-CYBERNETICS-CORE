import { createHash } from 'node:crypto';
export class OpportunityIntakeService {
    repository;
    constructor(repository) {
        this.repository = repository;
    }
    async ingest(envelope) {
        validateOpportunity(envelope.opportunity);
        const normalized = normalizeOpportunity(envelope.opportunity);
        const canonicalHash = hashOpportunity(normalized);
        const result = await this.repository.ingest(normalized, canonicalHash);
        await this.repository.appendEvent(`opportunity.${result.disposition}`, normalized.eventId, {
            sourceRunId: envelope.sourceRunId,
            canonicalHash,
            revision: result.stored.revision,
            changedFields: result.changedFields,
            opportunity: normalized
        });
        return { sourceRunId: envelope.sourceRunId, eventId: normalized.eventId, canonicalHash, result };
    }
}
export function normalizeOpportunity(input) {
    const provenance = [...input.provenance]
        .map((source) => ({ ...source, system: source.system.trim(), url: source.url.trim() }))
        .sort((a, b) => `${a.system}:${a.url}`.localeCompare(`${b.system}:${b.url}`));
    return {
        ...input,
        title: compact(input.title),
        issuer: compact(input.issuer),
        jurisdiction: compact(input.jurisdiction),
        summary: compact(input.summary),
        eligibility: unique(input.eligibility.map(compact)),
        requiredRegistrations: unique(input.requiredRegistrations.map(compact)),
        provenance
    };
}
export function hashOpportunity(input) {
    const stable = {
        ...input,
        provenance: input.provenance.map(({ retrievedAt, ...source }) => source)
    };
    return createHash('sha256').update(JSON.stringify(stable)).digest('hex');
}
function validateOpportunity(input) {
    if (input.schemaVersion !== '1.0.0')
        throw new Error(`Unsupported schema version: ${input.schemaVersion}`);
    for (const [field, value] of Object.entries({ eventId: input.eventId, externalId: input.externalId, title: input.title, issuer: input.issuer, jurisdiction: input.jurisdiction, summary: input.summary })) {
        if (!value?.trim())
            throw new Error(`Missing required field: ${field}`);
    }
    if (!input.provenance.length)
        throw new Error('At least one provenance source is required');
    if (input.deadline && Number.isNaN(Date.parse(input.deadline)))
        throw new Error('Invalid deadline');
}
function compact(value) { return value.trim().replace(/\s+/g, ' '); }
function unique(values) { return [...new Set(values.filter(Boolean))].sort(); }
