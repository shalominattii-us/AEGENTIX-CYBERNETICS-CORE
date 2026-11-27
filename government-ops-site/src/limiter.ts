export const DEMO_LIMIT = 20;
export const DEMO_WINDOW_MS = 60_000;
/** Enough for MAX_TEXT_CHARS under UTF-8, JSON wrapping, and escape expansion. */
export const MAX_BODY_BYTES = 65_536;
export const MAX_TEXT_CHARS = 12_000;
/** Cap in-isolate fallback buckets so a flood of IPs cannot grow the Map forever. */
export const MAX_BUCKETS = 2_000;

interface Bucket {
  count: number;
  resetAt: number;
}

// Per-isolate soft gate only. Durable limiting is env.DEMO_RATE_LIMITER (see index.ts).
// Worker eviction clears this Map; that is expected. Do not treat it as the only limit.
const buckets = new Map<string, Bucket>();

/** Test helper. Production code never resets the isolate map. */
export function resetDemoLimiter(): void {
  buckets.clear();
}

export function allowDemoRequest(key: string, now: number): boolean {
  if (buckets.size > MAX_BUCKETS) {
    for (const [storedKey, bucket] of buckets) {
      if (now >= bucket.resetAt) buckets.delete(storedKey);
    }
    if (buckets.size > MAX_BUCKETS) {
      const oldest = buckets.keys().next().value;
      if (oldest) buckets.delete(oldest);
    }
  }
  const current = buckets.get(key);
  if (!current || now >= current.resetAt) {
    buckets.set(key, { count: 1, resetAt: now + DEMO_WINDOW_MS });
    return true;
  }
  if (current.count >= DEMO_LIMIT) return false;
  current.count += 1;
  return true;
}
