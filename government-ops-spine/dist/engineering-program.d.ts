import type { BrainPlan, BuildSpecification, CapabilityMatch, TreasuryAnalysis } from './types.js';
export type EngineeringArtifactType = 'architecture' | 'subsystems' | 'interfaces' | 'risk_register' | 'verification_plan' | 'simulation_plan' | 'manufacturing_plan' | 'documentation_plan' | 'patent_candidate_package' | 'proposal_draft';
export interface EngineeringArtifact {
    artifactId: string;
    opportunityId: string;
    specificationId: string;
    type: EngineeringArtifactType;
    title: string;
    content: Record<string, unknown>;
    contentHash: string;
    createdAt: string;
    approvalState: 'draft' | 'technical_review' | 'authorized';
    externalActionBlocked: true;
}
export interface EngineeringProgram {
    programId: string;
    opportunityId: string;
    specificationId: string;
    planId: string;
    artifacts: EngineeringArtifact[];
    capabilityMatches: CapabilityMatch[];
    generatedAt: string;
    externalActionsBlocked: true;
}
export declare class EngineeringProgramGenerator {
    generate(input: {
        analysis: TreasuryAnalysis;
        specification: BuildSpecification;
        plan: BrainPlan;
        capabilityMatches?: CapabilityMatch[];
    }): EngineeringProgram;
}
