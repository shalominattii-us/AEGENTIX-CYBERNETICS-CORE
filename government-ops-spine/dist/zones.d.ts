export declare const EXECUTION_ZONES: readonly ["KERNEL", "TREASURY", "AI", "SECURITY", "XR", "DATA", "CLOUD", "GOVERNMENT_OPS", "PLATFORM", "MONITORING"];
export type ExecutionZone = typeof EXECUTION_ZONES[number];
export declare function getExecutionZones(): readonly string[];
export declare function isValidZone(zone: string): boolean;
