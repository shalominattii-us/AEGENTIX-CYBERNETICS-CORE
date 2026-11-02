export const EXECUTION_ZONES = [
  'KERNEL',
  'TREASURY', 
  'AI',
  'SECURITY',
  'XR',
  'DATA',
  'CLOUD',
  'GOVERNMENT_OPS',
  'PLATFORM',
  'MONITORING'
] as const;

export type ExecutionZone = typeof EXECUTION_ZONES[number];

export function getExecutionZones(): readonly string[] {
  const envZones = process.env.EXECUTION_ZONES;
  if (envZones) {
    return envZones.split(',').map(z => z.trim()).filter(Boolean);
  }
  return EXECUTION_ZONES;
}

export function isValidZone(zone: string): boolean {
  return getExecutionZones().includes(zone);
}
