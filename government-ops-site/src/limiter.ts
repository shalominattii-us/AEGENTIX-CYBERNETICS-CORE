export const DEMO_LIMIT = 20;
export const DEMO_WINDOW_MS = 60_000;
export const MAX_BODY_BYTES = 16_384;
export const MAX_TEXT_CHARS = 12_000;

interface Bucket {
  count: number;
  resetAt: number;
}

const buckets = new Map<string, Bucket>();

export function resetDemoLimiter(): void {
  buckets.clear();
}

export function allowDemoRequest(key: string, now: number): boolean {
  if (buckets.size > 2000) {
    for (const [storedKey, bucket] of buckets) {
      if (now >= bucket.resetAt) buckets.delete(storedKey);
    }
    if (buckets.size > 2000) {
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
