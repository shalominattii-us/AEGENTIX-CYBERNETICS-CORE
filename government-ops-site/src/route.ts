import { analyzeDemo, listSamples } from "./analyze.js";
import { clientKey, HttpError, json } from "./http.js";
import { allowDemoRequest, DEMO_WINDOW_MS, MAX_BODY_BYTES, MAX_TEXT_CHARS } from "./limiter.js";
import { seal } from "./headers.js";
import { readSnapshot } from "./snapshot.js";

export interface SiteDeps {
  fetchAsset(request: Request): Promise<Response>;
  limitDemo(key: string): Promise<boolean>;
  now(): number;
  siteMode: string;
}

export async function route(request: Request, deps: SiteDeps): Promise<Response> {
  const started = deps.now();
  let response: Response;
  try {
    response = await dispatch(request, deps);
  } catch (error) {
    if (error instanceof HttpError) {
      response = json(request, error.status, { ...error.body, externalActionsBlocked: true }, error.headers);
    } else {
      console.error(JSON.stringify({
        event: "government_ops_site.error",
        message: error instanceof Error ? error.message : "unknown error",
      }));
      response = json(request, 500, {
        error: "The public site could not complete that request.",
        externalActionsBlocked: true,
      });
    }
  }
  const url = new URL(request.url);
  if (url.pathname.startsWith("/api/")) {
    console.log(JSON.stringify({
      event: "government_ops_site.request",
      method: request.method,
      path: url.pathname,
      status: response.status,
      durationMs: deps.now() - started,
    }));
  }
  return response;
}

async function dispatch(request: Request, deps: SiteDeps): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname;
  if (path.startsWith("/api/")) return dispatchApi(request, deps, path);
  if (request.method !== "GET" && request.method !== "HEAD") {
    throw new HttpError(405, { error: "This public site only reads pages with GET." }, { allow: "GET, HEAD" });
  }
  if (path === "/snapshot/opportunities.json") return snapshotResponse(request, deps);
  const asset = await deps.fetchAsset(request);
  if (asset.status === 404 && path !== "/404.html") {
    const fallbackUrl = new URL("/404.html", request.url);
    const fallback = await deps.fetchAsset(new Request(fallbackUrl, { method: "GET" }));
    if (fallback.ok) {
      return seal(request, new Response(fallback.body, { status: 404, headers: fallback.headers }));
    }
  }
  const headers = new Headers();
  if (asset.headers.get("content-type")?.includes("text/html")) headers.set("cache-control", "no-cache");
  return seal(request, asset, headers);
}

async function dispatchApi(request: Request, deps: SiteDeps, path: string): Promise<Response> {
  if (path === "/api/health" && request.method === "GET") {
    return json(request, 200, {
      ok: true,
      service: "government-ops-site",
      mode: deps.siteMode,
      externalActionsBlocked: true,
      snapshot: "static-sample",
      reads: "static-snapshot-and-sample-text",
    });
  }
  if (path === "/api/demo/samples" && request.method === "GET") {
    return json(request, 200, { ...listSamples(), externalActionsBlocked: true });
  }
  if (path === "/api/demo/analyze" && request.method === "POST") return analyze(request, deps);
  if (path === "/api/opportunities" && request.method === "GET") return snapshotResponse(request, deps);
  const record = path.match(/^\/api\/opportunities\/([^/]+)$/);
  if (record && request.method === "GET") return oneOpportunity(request, deps, record[1]);
  if (request.method !== "GET" && request.method !== "HEAD" && request.method !== "POST") {
    throw new HttpError(405, { error: "Method not allowed." }, { allow: "GET, POST" });
  }
  throw new HttpError(404, { error: "Not found." });
}

async function analyze(request: Request, deps: SiteDeps): Promise<Response> {
  const key = clientKey(request);
  if (!allowDemoRequest(key, deps.now())) {
    throw new HttpError(429, { error: "Too many demo requests from this network. Wait and try again." }, {
      "retry-after": String(Math.ceil(DEMO_WINDOW_MS / 1000)),
    });
  }
  let allowed = false;
  try {
    allowed = await deps.limitDemo(key);
  } catch (error) {
    console.error(JSON.stringify({
      event: "government_ops_site.rate_limit_unavailable",
      message: error instanceof Error ? error.message : "rate limiter unavailable",
    }));
    throw new HttpError(503, { error: "The demo is temporarily unavailable." });
  }
  if (!allowed) {
    throw new HttpError(429, { error: "Too many demo requests from this network. Wait and try again." }, {
      "retry-after": String(Math.ceil(DEMO_WINDOW_MS / 1000)),
    });
  }
  const raw = await readBoundedBody(request);
  let payload: unknown;
  try {
    payload = JSON.parse(raw);
  } catch {
    throw new HttpError(400, { error: "Demo requests must be JSON." });
  }
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new HttpError(400, { error: "Demo requests must be a JSON object." });
  }
  const body = payload as Record<string, unknown>;
  const sampleId = typeof body.sampleId === "string" ? body.sampleId.slice(0, 40) : undefined;
  const text = typeof body.text === "string" ? body.text : undefined;
  if (text && text.trim().length > MAX_TEXT_CHARS) {
    throw new HttpError(400, { error: `Solicitation text is limited to ${MAX_TEXT_CHARS} characters.` });
  }
  try {
    const result = await analyzeDemo({ text, sampleId });
    return json(request, 200, result);
  } catch (error) {
    if (error instanceof HttpError) throw error;
    const message = error instanceof Error ? error.message : "";
    if (message.startsWith("Paste solicitation")) throw new HttpError(400, { error: message });
    if (message.includes("failed open")) throw error;
    throw new HttpError(400, { error: "The demo could not read that solicitation text." });
  }
}

async function readBoundedBody(request: Request): Promise<string> {
  const contentType = request.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().startsWith("application/json")) {
    throw new HttpError(415, { error: "Demo requests must use application/json." });
  }
  const declared = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(declared) && declared > MAX_BODY_BYTES) {
    throw new HttpError(413, { error: "Demo request body is too large." });
  }
  const raw = await request.text();
  if (raw.length > MAX_BODY_BYTES) throw new HttpError(413, { error: "Demo request body is too large." });
  return raw;
}

async function snapshotResponse(request: Request, deps: SiteDeps): Promise<Response> {
  const snapshot = await readSnapshot(deps.fetchAsset, request.url);
  const path = new URL(request.url).pathname;
  const body = path.startsWith("/api/") ? { ...snapshot, externalActionsBlocked: true as const } : snapshot;
  const headers = path === "/snapshot/opportunities.json" ? { "cache-control": "public, max-age=60" } : undefined;
  return json(request, 200, body, headers);
}

async function oneOpportunity(request: Request, deps: SiteDeps, rawId: string): Promise<Response> {
  let id: string;
  try {
    id = decodeURIComponent(rawId);
  } catch {
    throw new HttpError(400, { error: "Opportunity id is invalid." });
  }
  if (!/^SAMPLE-[A-Z0-9-]{2,40}$/.test(id)) throw new HttpError(404, { error: "Not found." });
  const snapshot = await readSnapshot(deps.fetchAsset, request.url);
  const record = snapshot.records.find((item) => item.id === id);
  if (!record) throw new HttpError(404, { error: "Not found." });
  return json(request, 200, {
    label: snapshot.label,
    fictional: true,
    disclaimer: snapshot.disclaimer,
    externalActionsBlocked: true,
    record,
  });
}
