import type { OpportunityRepository } from './repository.js';
export interface RuntimeRequest {
    method: string;
    path: string;
    body?: unknown;
}
export interface RuntimeResponse {
    status: number;
    body: unknown;
}
export declare class GovernmentOpsRuntime {
    private readonly repository;
    private readonly intake;
    constructor(repository: OpportunityRepository);
    handle(request: RuntimeRequest): Promise<RuntimeResponse>;
    private analyzeAndPlan;
}
