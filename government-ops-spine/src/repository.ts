import { BrainPlan, BuildSpecification, PublicOpportunity, TreasuryAnalysis } from './types.js';

export type IngestDisposition = 'created'|'unchanged'|'amended'|'cancelled'|'awarded';

export interface StoredOpportunity {
  opportunity: PublicOpportunity;
  canonicalHash: string;
  revision: number;
  status: 'active'|'cancelled'|'awarded'|'closed';
}

export interface IngestResult {
  disposition: IngestDisposition;
  stored: StoredOpportunity;
  changedFields: string[];
}

export interface OpportunityRepository {
  getByEventId(eventId: string): Promise<StoredOpportunity | undefined>;
  getBySourceIdentity(sourceSystem: string, externalId: string): Promise<StoredOpportunity | undefined>;
  ingest(opportunity: PublicOpportunity, canonicalHash: string): Promise<IngestResult>;
  saveAnalysis(analysis: TreasuryAnalysis): Promise<void>;
  saveSpecification(specification: BuildSpecification): Promise<void>;
  saveBrainPlan(plan: BrainPlan): Promise<void>;
  appendEvent(eventType: string, aggregateId: string, payload: unknown): Promise<void>;
}

export class MemoryOpportunityRepository implements OpportunityRepository {
  private readonly opportunities = new Map<string, StoredOpportunity>();
  private readonly sourceIndex = new Map<string, string>();

  async getByEventId(eventId: string): Promise<StoredOpportunity | undefined> {
    return this.opportunities.get(eventId);
  }

  async getBySourceIdentity(sourceSystem: string, externalId: string): Promise<StoredOpportunity | undefined> {
    const eventId = this.sourceIndex.get(`${sourceSystem}:${externalId}`);
    return eventId ? this.opportunities.get(eventId) : undefined;
  }

  async ingest(opportunity: PublicOpportunity, canonicalHash: string): Promise<IngestResult> {
    const sourceSystem = opportunity.provenance[0]?.system ?? 'unknown';
    const existing = await this.getBySourceIdentity(sourceSystem, opportunity.externalId);
    if (!existing) {
      const stored: StoredOpportunity = { opportunity, canonicalHash, revision: 1, status: inferStatus(opportunity) };
      this.opportunities.set(opportunity.eventId, stored);
      this.sourceIndex.set(`${sourceSystem}:${opportunity.externalId}`, opportunity.eventId);
      return { disposition: statusDisposition(stored.status, 'created'), stored, changedFields: [] };
    }
    if (existing.canonicalHash === canonicalHash) return { disposition: 'unchanged', stored: existing, changedFields: [] };
    const changedFields = diffFields(existing.opportunity, opportunity);
    const stored: StoredOpportunity = { opportunity, canonicalHash, revision: existing.revision + 1, status: inferStatus(opportunity) };
    this.opportunities.delete(existing.opportunity.eventId);
    this.opportunities.set(opportunity.eventId, stored);
    this.sourceIndex.set(`${sourceSystem}:${opportunity.externalId}`, opportunity.eventId);
    return { disposition: statusDisposition(stored.status, 'amended'), stored, changedFields };
  }

  async saveAnalysis(_: TreasuryAnalysis): Promise<void> {}
  async saveSpecification(_: BuildSpecification): Promise<void> {}
  async saveBrainPlan(_: BrainPlan): Promise<void> {}
  async appendEvent(_: string, __: string, ___: unknown): Promise<void> {}
}

function inferStatus(opportunity: PublicOpportunity): StoredOpportunity['status'] {
  const text = `${opportunity.title} ${opportunity.summary}`.toLowerCase();
  if (text.includes('cancelled') || text.includes('canceled')) return 'cancelled';
  if (text.includes('award notice') || text.includes('awarded')) return 'awarded';
  if (opportunity.deadline && Date.parse(opportunity.deadline) < Date.now()) return 'closed';
  return 'active';
}

function statusDisposition(status: StoredOpportunity['status'], fallback: 'created'|'amended'): IngestDisposition {
  if (status === 'cancelled') return 'cancelled';
  if (status === 'awarded') return 'awarded';
  return fallback;
}

function diffFields(before: PublicOpportunity, after: PublicOpportunity): string[] {
  const fields: Array<keyof PublicOpportunity> = ['title','issuer','jurisdiction','opportunityType','publicationDate','updateDate','deadline','value','eligibility','setAside','location','submissionMethod','requiredRegistrations','summary','rawText','provenance'];
  return fields.filter((field) => JSON.stringify(before[field]) !== JSON.stringify(after[field])).map(String);
}
