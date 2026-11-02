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
];
export function getExecutionZones() {
    const envZones = process.env.EXECUTION_ZONES;
    if (envZones) {
        return envZones.split(',').map(z => z.trim()).filter(Boolean);
    }
    return EXECUTION_ZONES;
}
export function isValidZone(zone) {
    return getExecutionZones().includes(zone);
}
