import { BrainPlan, BuildSpecification, PublicOpportunity, TreasuryAnalysis } from './types.js';
import { IntakeReceipt } from './intake.js';

export interface ApiError { code:string; message:string; details?:unknown; }
export type ApiResponse<T> = { ok:true; data:T } | { ok:false; error:ApiError };

export interface IngestOpportunityRequest { sourceRunId:string; receivedAt:string; opportunity:PublicOpportunity; }
export type IngestOpportunityResponse = ApiResponse<IntakeReceipt>;

export interface AnalyzeOpportunityRequest { opportunityId:string; force?:boolean; }
export type AnalyzeOpportunityResponse = ApiResponse<TreasuryAnalysis>;

export interface BuildPlanRequest { opportunityId:string; requestedZones?:BuildSpecification['executionZones']; }
export type BuildPlanResponse = ApiResponse<{ specification:BuildSpecification; plan:BrainPlan }>;

export interface OpportunityStateResponse {
  opportunity: PublicOpportunity;
  status: 'active'|'closed'|'cancelled'|'awarded';
  revision: number;
  analysis?: TreasuryAnalysis;
  specification?: BuildSpecification;
  plan?: BrainPlan;
  externalActionsBlocked: true;
}

export const CYBERCORE_ROUTES = {
  ingest: 'POST /api/opportunities/ingest',
  analyze: 'POST /api/opportunities/:id/analyze',
  buildPlan: 'POST /api/opportunities/:id/build-plan',
  state: 'GET /api/opportunities/:id/state',
  health: 'GET /health'
} as const;
