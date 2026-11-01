export class MemoryOpportunityRepository {
    opportunities = new Map();
    sourceIndex = new Map();
    async getByEventId(eventId) {
        return this.opportunities.get(eventId);
    }
    async getBySourceIdentity(sourceSystem, externalId) {
        const eventId = this.sourceIndex.get(`${sourceSystem}:${externalId}`);
        return eventId ? this.opportunities.get(eventId) : undefined;
    }
    async ingest(opportunity, canonicalHash) {
        const sourceSystem = opportunity.provenance[0]?.system ?? 'unknown';
        const existing = await this.getBySourceIdentity(sourceSystem, opportunity.externalId);
        if (!existing) {
            const stored = { opportunity, canonicalHash, revision: 1, status: inferStatus(opportunity) };
            this.opportunities.set(opportunity.eventId, stored);
            this.sourceIndex.set(`${sourceSystem}:${opportunity.externalId}`, opportunity.eventId);
            return { disposition: statusDisposition(stored.status, 'created'), stored, changedFields: [] };
        }
        if (existing.canonicalHash === canonicalHash)
            return { disposition: 'unchanged', stored: existing, changedFields: [] };
        const changedFields = diffFields(existing.opportunity, opportunity);
        const stored = { opportunity, canonicalHash, revision: existing.revision + 1, status: inferStatus(opportunity) };
        this.opportunities.delete(existing.opportunity.eventId);
        this.opportunities.set(opportunity.eventId, stored);
        this.sourceIndex.set(`${sourceSystem}:${opportunity.externalId}`, opportunity.eventId);
        return { disposition: statusDisposition(stored.status, 'amended'), stored, changedFields };
    }
    async saveAnalysis(_) { }
    async saveSpecification(_) { }
    async saveBrainPlan(_) { }
    async appendEvent(_, __, ___) { }
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
function statusDisposition(status, fallback) {
    if (status === 'cancelled')
        return 'cancelled';
    if (status === 'awarded')
        return 'awarded';
    return fallback;
}
function diffFields(before, after) {
    const fields = ['title', 'issuer', 'jurisdiction', 'opportunityType', 'publicationDate', 'updateDate', 'deadline', 'value', 'eligibility', 'setAside', 'location', 'submissionMethod', 'requiredRegistrations', 'summary', 'rawText', 'provenance'];
    return fields.filter((field) => JSON.stringify(before[field]) !== JSON.stringify(after[field])).map(String);
}
