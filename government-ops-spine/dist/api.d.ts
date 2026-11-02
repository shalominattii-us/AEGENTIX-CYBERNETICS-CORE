import { BrainPlan, BuildSpecification, PublicOpportunity, TreasuryAnalysis } from './types.js';
import { IntakeReceipt } from './intake.js';
export interface ApiError {
    code: string;
    message: string;
    details?: unknown;
}
export type ApiResponse<T> = {
    ok: true;
    data: T;
} | {
    ok: false;
    error: ApiError;
};
export interface IngestOpportunityRequest {
    sourceRunId: string;
    receivedAt: string;
    opportunity: PublicOpportunity;
}
export type IngestOpportunityResponse = ApiResponse<IntakeReceipt>;
export interface AnalyzeOpportunityRequest {
    opportunityId: string;
    force?: boolean;
}
export type AnalyzeOpportunityResponse = ApiResponse<TreasuryAnalysis>;
export interface BuildPlanRequest {
    opportunityId: string;
    requestedZones?: string[];
}
export type BuildPlanResponse = ApiResponse<{
    specification: BuildSpecification;
    plan: BrainPlan;
}>;
export interface OpportunityStateResponse {
    opportunity: PublicOpportunity;
    status: 'active' | 'closed' | 'cancelled' | 'awarded';
    revision: number;
    analysis?: TreasuryAnalysis;
    specification?: BuildSpecification;
    plan?: BrainPlan;
    externalActionsBlocked: true;
}
export declare const CYBERCORE_ROUTES: {
    readonly ingest: "POST /api/opportunities/ingest";
    readonly analyze: "POST /api/opportunities/:id/analyze";
    readonly buildPlan: "POST /api/opportunities/:id/build-plan";
    readonly state: "GET /api/opportunities/:id/state";
    readonly health: "GET /health";
};
