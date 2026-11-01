import type { Pool } from 'pg';
import { type EngineeringProgram } from './engineering-program.js';
export declare class PostgresEngineeringProgramService {
    private readonly pool;
    private readonly generator;
    constructor(pool: Pool);
    generateForOpportunity(opportunityId: string): Promise<EngineeringProgram>;
    get(programId: string): Promise<EngineeringProgram | undefined>;
    listByOpportunity(opportunityId: string): Promise<Array<{
        programId: string;
        generatedAt: string;
        artifactCount: number;
    }>>;
    private save;
}
