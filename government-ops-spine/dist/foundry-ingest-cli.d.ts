import { type OpportunitySink } from './foundry-bridge.js';
export interface FoundryCliIO {
    env?: NodeJS.ProcessEnv;
    stdout?: (line: string) => void;
    stderr?: (line: string) => void;
    fetchImpl?: typeof fetch;
    sink?: OpportunitySink;
    now?: () => Date;
}
export declare function runFoundryIngestCli(argv: string[], io?: FoundryCliIO): Promise<number>;
