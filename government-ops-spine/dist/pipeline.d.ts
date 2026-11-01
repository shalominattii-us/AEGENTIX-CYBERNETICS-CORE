import type { BrainPlan, BuildSpecification, CapabilityMatch, CapabilityRecord, PublicOpportunity, TreasuryAnalysis } from './types.js';
export declare function parseOpportunity(opportunity: PublicOpportunity): TreasuryAnalysis;
export declare function generateBuildSpecification(a: TreasuryAnalysis): BuildSpecification;
export declare function createBrainPlan(s: BuildSpecification): BrainPlan;
export declare function matchCapabilities(a: TreasuryAnalysis, capabilities: CapabilityRecord[]): CapabilityMatch[];
export declare function assertExternalActionAuthorized(action: 'submit_offer' | 'file_patent' | 'commit_funds' | 'external_representation', authorizationToken?: string): void;
export declare function runInternalPipeline(opportunity: PublicOpportunity, capabilities?: CapabilityRecord[]): {
    analysis: TreasuryAnalysis;
    specification: BuildSpecification;
    plan: BrainPlan;
    matches: CapabilityMatch[];
};
