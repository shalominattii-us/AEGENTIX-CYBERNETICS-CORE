const DEFAULT_ENDPOINT = 'https://api.sam.gov/opportunities/v2/search';
const DEFAULT_TIMEOUT_MS = 30_000;

export interface SamGovSearchRequest {
  apiKey: string;
  postedFrom: string;
  postedTo: string;
  limit?: number;
  offset?: number;
  naics?: string;
  title?: string;
  noticeType?: string;
  organization?: string;
  endpoint?: string;
  timeoutMs?: number;
  maxPages?: number;
  fetchImpl?: typeof fetch;
}

export function redactSecrets(text: string, secrets: readonly string[]): string {
  let redacted = text;
  const patterns = [/([?&#]api_key=)[^&\s#]+/gi, /(api_key(?:=|%3D|":\s*"))[^&\s"',}]+/gi];
  for (const secret of secrets) {
    const trimmed = secret.trim();
    if (trimmed.length < 8) continue;
    redacted = redacted.split(trimmed).join('[redacted]');
  }
  for (const pattern of patterns) redacted = redacted.replace(pattern, '$1[redacted]');
  return redacted;
}

export function assertOfficialSamEndpoint(endpoint: string): URL {
  let url: URL;
  try {
    url = new URL(endpoint);
  } catch {
    throw new Error('SAM.gov endpoint must be an https URL on api.sam.gov');
  }
  if (url.protocol !== 'https:' || url.hostname !== 'api.sam.gov') {
    throw new Error('SAM.gov endpoint host must be api.sam.gov');
  }
  return url;
}

export function formatSamDate(date: Date): string {
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  return `${month}/${day}/${date.getUTCFullYear()}`;
}

export function assertSamDate(value: string, label: string): string {
  if (!/^(0[1-9]|1[0-2])\/(0[1-9]|[12]\d|3[01])\/\d{4}$/.test(value)) {
    throw new Error(`${label} must use MM/dd/yyyy`);
  }
  return value;
}

export async function searchSamGov(request: SamGovSearchRequest): Promise<Record<string, unknown>[]> {
  const apiKey = request.apiKey.trim();
  if (!apiKey) throw new Error('SAM_GOV_API_KEY is required');
  const postedFrom = assertSamDate(request.postedFrom, 'postedFrom');
  const postedTo = assertSamDate(request.postedTo, 'postedTo');
  const limit = clamp(request.limit ?? 100, 1, 1000);
  const maxPages = clamp(request.maxPages ?? 5, 1, 50);
  const fetchImpl = request.fetchImpl ?? fetch;
  const endpoint = request.endpoint ?? DEFAULT_ENDPOINT;
  assertOfficialSamEndpoint(endpoint);

  const notices: Record<string, unknown>[] = [];
  let offset = request.offset ?? 0;
  if (offset < 0) throw new Error('offset cannot be negative');
  for (let page = 0; page < maxPages; page += 1) {
    const payload = await fetchSamPage({
      apiKey,
      endpoint,
      postedFrom,
      postedTo,
      limit,
      offset,
      naics: request.naics,
      title: request.title,
      noticeType: request.noticeType,
      organization: request.organization,
      timeoutMs: request.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      fetchImpl
    });
    const batch = payload.opportunitiesData ?? [];
    notices.push(...batch);
    const total = typeof payload.totalRecords === 'number' ? payload.totalRecords : offset + batch.length;
    offset += batch.length;
    if (batch.length === 0 || batch.length < limit || offset >= total) break;
  }
  return notices;
}

async function fetchSamPage(input: {
  apiKey: string;
  endpoint: string;
  postedFrom: string;
  postedTo: string;
  limit: number;
  offset: number;
  naics?: string;
  title?: string;
  noticeType?: string;
  organization?: string;
  timeoutMs: number;
  fetchImpl: typeof fetch;
}): Promise<{ totalRecords?: number; opportunitiesData: Record<string, unknown>[] }> {
  const url = new URL(input.endpoint);
  url.searchParams.set('api_key', input.apiKey);
  url.searchParams.set('postedFrom', input.postedFrom);
  url.searchParams.set('postedTo', input.postedTo);
  url.searchParams.set('limit', String(input.limit));
  url.searchParams.set('offset', String(input.offset));
  if (input.naics) url.searchParams.set('ncode', input.naics);
  if (input.title) url.searchParams.set('title', input.title);
  if (input.noticeType) url.searchParams.set('ptype', input.noticeType);
  if (input.organization) url.searchParams.set('organizationName', input.organization);

  let response: Response;
  try {
    response = await input.fetchImpl(url, {
      method: 'GET',
      redirect: 'manual',
      headers: {
        accept: 'application/json',
        'user-agent': 'government-ops-spine-sam-gov/1.0'
      },
      signal: AbortSignal.timeout(input.timeoutMs)
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`SAM.gov request failed: ${redactSecrets(message, [input.apiKey])}`);
  }
  if (response.status >= 300 && response.status < 400) {
    throw new Error(`SAM.gov redirect was not followed (${response.status})`);
  }
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`SAM.gov returned HTTP ${response.status}: ${redactSecrets(body.slice(0, 500), [input.apiKey])}`);
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(body);
  } catch {
    throw new Error('SAM.gov response was not valid JSON');
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('SAM.gov response must be a JSON object');
  }
  const record = parsed as Record<string, unknown>;
  const opportunities = record.opportunitiesData ?? [];
  if (!Array.isArray(opportunities)) throw new Error('SAM.gov response opportunitiesData must be a list');
  return {
    totalRecords: typeof record.totalRecords === 'number' ? record.totalRecords : undefined,
    opportunitiesData: opportunities.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object' && !Array.isArray(item))
  };
}

function clamp(value: number, min: number, max: number): number {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, Math.trunc(value)));
}
