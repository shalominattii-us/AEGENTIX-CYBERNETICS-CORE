import type { Pool, PoolClient, QueryResultRow } from 'pg';
import type { BrainPlan, BuildSpecification, PublicOpportunity, TreasuryAnalysis } from './types.js';
import type { IngestResult, OpportunityRepository, StoredOpportunity } from './repository.js';

export class PostgresOpportunityRepository implements OpportunityRepository {
  constructor(private readonly pool: Pool) {}

  async getByEventId(eventId: string): Promise<StoredOpportunity | undefined> {
    const result = await this.pool.query('select * from opportunity_records where event_id = $1', [eventId]);
    return result.rows[0] ? mapStored(result.rows[0]) : undefined;
  }

  async getBySourceIdentity(sourceSystem: string, externalId: string): Promise<StoredOpportunity | undefined> {
    const result = await this.pool.query(
      `select r.* from opportunity_records r join opportunity_provenance p on p.event_id=r.event_id
       where p.source_system=$1 and r.external_id=$2 order by r.revision desc limit 1`,
      [sourceSystem, externalId]
    );
    return result.rows[0] ? mapStored(result.rows[0]) : undefined;
  }

  async ingest(opportunity: PublicOpportunity, canonicalHash: string): Promise<IngestResult> {
    const client = await this.pool.connect();
    try {
      await client.query('begin');
      const sourceSystem = opportunity.provenance[0]?.system ?? 'unknown';
      const existing = await this.getBySourceIdentityTx(client, sourceSystem, opportunity.externalId);
      if (existing?.canonicalHash === canonicalHash) {
        await client.query('commit');
        return { disposition: 'unchanged', stored: existing, changedFields: [] };
      }
      const revision = (existing?.revision ?? 0) + 1;
      const status = inferStatus(opportunity);
      const changedFields = existing ? diffFields(existing.opportunity, opportunity) : [];
      await client.query(
        `insert into opportunity_records(event_id,external_id,title,issuer,jurisdiction,opportunity_type,publication_date,update_date,deadline,value_json,eligibility_json,set_aside,location,submission_method,required_registrations_json,summary,raw_text,canonical_hash,revision,status,opportunity_json)
         values($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)
         on conflict(event_id) do update set canonical_hash=excluded.canonical_hash, revision=excluded.revision, status=excluded.status, opportunity_json=excluded.opportunity_json, updated_at=now()`,
        [opportunity.eventId,opportunity.externalId,opportunity.title,opportunity.issuer,opportunity.jurisdiction,opportunity.opportunityType,opportunity.publicationDate??null,opportunity.updateDate??null,opportunity.deadline??null,opportunity.value??null,opportunity.eligibility,opportunity.setAside??null,opportunity.location??null,opportunity.submissionMethod??null,opportunity.requiredRegistrations,opportunity.summary,opportunity.rawText??null,canonicalHash,revision,status,opportunity]
      );
      for (const source of opportunity.provenance) {
        await client.query(
          `insert into opportunity_provenance(event_id,source_system,authority,url,retrieved_at,content_hash,attachment_urls)
           values($1,$2,$3,$4,$5,$6,$7) on conflict do nothing`,
          [opportunity.eventId,source.system,source.authority,source.url,source.retrievedAt,source.contentHash??null,source.attachmentUrls??[]]
        );
      }
      await client.query(
        `insert into opportunity_revisions(event_id,revision,canonical_hash,changed_fields,opportunity_json) values($1,$2,$3,$4,$5)`,
        [opportunity.eventId,revision,canonicalHash,changedFields,opportunity]
      );
      await client.query('commit');
      const stored: StoredOpportunity = { opportunity, canonicalHash, revision, status };
      return { disposition: status === 'cancelled' ? 'cancelled' : status === 'awarded' ? 'awarded' : existing ? 'amended' : 'created', stored, changedFields };
    } catch (error) {
      await client.query('rollback');
      throw error;
    } finally { client.release(); }
  }

  async saveAnalysis(analysis: TreasuryAnalysis): Promise<void> {
    await this.pool.query(`insert into treasury_analyses(opportunity_id,analysis_json) values($1,$2) on conflict(opportunity_id) do update set analysis_json=excluded.analysis_json, updated_at=now()`, [analysis.opportunityId, analysis]);
  }
  async saveSpecification(specification: BuildSpecification): Promise<void> {
    await this.pool.query(`insert into build_specifications(specification_id,opportunity_id,specification_json) values($1,$2,$3) on conflict(specification_id) do update set specification_json=excluded.specification_json, updated_at=now()`, [specification.specificationId, specification.opportunityId, specification]);
  }
  async saveBrainPlan(plan: BrainPlan): Promise<void> {
    await this.pool.query(`insert into brain_plans(plan_id,specification_id,plan_json) values($1,$2,$3) on conflict(plan_id) do update set plan_json=excluded.plan_json, updated_at=now()`, [plan.planId, plan.specificationId, plan]);
  }
  async appendEvent(eventType: string, aggregateId: string, payload: unknown): Promise<void> {
    await this.pool.query(`insert into cybercore_outbox(event_type,aggregate_id,payload_json) values($1,$2,$3)`, [eventType, aggregateId, payload]);
  }

  private async getBySourceIdentityTx(client: PoolClient, sourceSystem: string, externalId: string): Promise<StoredOpportunity | undefined> {
    const result = await client.query(
      `select r.* from opportunity_records r join opportunity_provenance p on p.event_id=r.event_id where p.source_system=$1 and r.external_id=$2 order by r.revision desc limit 1 for update`,
      [sourceSystem, externalId]
    );
    return result.rows[0] ? mapStored(result.rows[0]) : undefined;
  }
}

function mapStored(row: QueryResultRow): StoredOpportunity { return { opportunity: row.opportunity_json, canonicalHash: row.canonical_hash, revision: row.revision, status: row.status }; }
function inferStatus(opportunity: PublicOpportunity): StoredOpportunity['status'] { const text=`${opportunity.title} ${opportunity.summary}`.toLowerCase(); if(/cancell?ed/.test(text)) return 'cancelled'; if(/award notice|awarded/.test(text)) return 'awarded'; if(opportunity.deadline && Date.parse(opportunity.deadline)<Date.now()) return 'closed'; return 'active'; }
function diffFields(before: PublicOpportunity, after: PublicOpportunity): string[] { return (Object.keys(after) as Array<keyof PublicOpportunity>).filter((k)=>JSON.stringify(before[k])!==JSON.stringify(after[k])).map(String); }
