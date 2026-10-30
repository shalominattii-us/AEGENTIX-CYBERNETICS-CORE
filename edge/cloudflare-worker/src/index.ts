/**
 * AEGENTIX Edge Gateway – Cloudflare Worker
 * Sovereign Machine Economy Systems
 *
 * Deploy with: npx wrangler deploy
 * Requires: Cloudflare Tunnel pointing to your origin (Docker stack)
 */

export interface Env {
  ORIGIN_API: string;               // e.g. "https://api-internal.aegentix.example" (Tunnel hostname)
  CAPABILITY_SECRET: string;        // HMAC secret for capability tokens
  SOVEREIGN_TOKEN: string;          // Master token for elevated actions (keep in Secrets)
  ENVIRONMENT: "production" | "staging" | "development";
}

interface HealthStatus {
  service: string;
  status: "operational" | "degraded" | "down";
  latencyMs?: number;
  details?: string;
}

interface AegentixStatus {
  system: "AEGENTIX";
  version: string;
  environment: string;
  timestamp: string;
  overall: "operational" | "degraded" | "down";
  valueStatePolicy: "SIMULATED_NEVER_PRESENTED_AS_SETTLED";
  humanAuthorization: "REQUIRED_ABOVE_AUTONOMOUS_EXECUTION";
  services: HealthStatus[];
  message: string;
}

const SYSTEM_VERSION = "2026.10.27-edge";

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders() });
    }

    try {
      if (path === "/health" || path === "/status" || path === "/") {
        return await handleStatus(env);
      }

      if (path.startsWith("/api/")) {
        return await handleProxy(request, env, path);
      }

      if (path.startsWith("/sovereign/")) {
        return await handleSovereign(request, env, path);
      }

      return json({ error: "Not found", system: "AEGENTIX" }, 404);
    } catch (err: any) {
      console.error("AEGENTIX Worker error:", err);
      return json({
        error: "Internal edge error",
        message: err.message || "Unknown",
        system: "AEGENTIX",
      }, 500);
    }
  },

  async scheduled(event: ScheduledEvent, env: Env, ctx: ExecutionContext) {
    console.log(`[AEGENTIX Cron] Triggered at ${new Date().toISOString()}`);
    // await fetch(`${env.ORIGIN_API}/api/cybercore/settlement/batch`, { ... });
  },
};

async function handleStatus(env: Env): Promise<Response> {
  const services: HealthStatus[] = [];

  const originCheck = await checkService("origin-api", env.ORIGIN_API + "/api/cybercore/treasury/status");
  services.push(originCheck);

  const overall = services.every(s => s.status === "operational")
    ? "operational"
    : services.some(s => s.status === "operational")
      ? "degraded"
      : "down";

  const body: AegentixStatus = {
    system: "AEGENTIX",
    version: SYSTEM_VERSION,
    environment: env.ENVIRONMENT || "production",
    timestamp: new Date().toISOString(),
    overall,
    valueStatePolicy: "SIMULATED_NEVER_PRESENTED_AS_SETTLED",
    humanAuthorization: "REQUIRED_ABOVE_AUTONOMOUS_EXECUTION",
    services,
    message: overall === "operational"
      ? "AEGENTIX edge gateway operational. Human authorization remains above autonomous execution."
      : "AEGENTIX edge reports degraded or down state. Investigate origin.",
  };

  return json(body, overall === "down" ? 503 : 200);
}

async function handleProxy(request: Request, env: Env, path: string): Promise<Response> {
  const authHeader = request.headers.get("Authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");

  const isPublicRead = request.method === "GET" && (
    path.includes("/treasury/status") ||
    path.includes("/rewards/summary") ||
    path.includes("/vault/shards") ||
    path.includes("/health")
  );

  if (!isPublicRead && !token) {
    return json({ error: "Capability token required", system: "AEGENTIX" }, 401);
  }

  const originUrl = env.ORIGIN_API + path + (new URL(request.url).search || "");

  const headers = new Headers(request.headers);
  headers.set("X-AEGENTIX-Edge", "cloudflare-worker");
  headers.set("X-AEGENTIX-Value-Policy", "SIMULATED_NEVER_PRESENTED_AS_SETTLED");

  const originRequest = new Request(originUrl, {
    method: request.method,
    headers,
    body: request.method !== "GET" && request.method !== "HEAD" ? request.body : null,
    redirect: "manual",
  });

  const response = await fetch(originRequest);

  const newHeaders = new Headers(response.headers);
  newHeaders.set("X-AEGENTIX-Edge", "cloudflare-worker");
  newHeaders.set("X-AEGENTIX-Timestamp", new Date().toISOString());
  newHeaders.set("Access-Control-Allow-Origin", "*");

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: newHeaders,
  });
}

async function handleSovereign(request: Request, env: Env, path: string): Promise<Response> {
  const authHeader = request.headers.get("Authorization") || "";
  const token = authHeader.replace(/^Bearer\s+/i, "");

  if (token !== env.SOVEREIGN_TOKEN) {
    return json({ error: "Sovereign authorization required", system: "AEGENTIX" }, 403);
  }

  if (path === "/sovereign/kill-switch" && request.method === "POST") {
    const res = await fetch(`${env.ORIGIN_API}/api/cybercore/circuit-breaker/activate`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.SOVEREIGN_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ reason: "Sovereign kill-switch activated via edge", timestamp: new Date().toISOString() }),
    });
    return json({ message: "Kill-switch signal sent", status: res.status }, res.status);
  }

  return json({ error: "Unknown sovereign action", system: "AEGENTIX" }, 404);
}

async function checkService(name: string, url: string): Promise<HealthStatus> {
  const start = Date.now();
  try {
    const res = await fetch(url, {
      method: "GET",
      headers: { "User-Agent": "AEGENTIX-Edge-Health/1.0" },
      signal: AbortSignal.timeout(4000),
    });
    const latency = Date.now() - start;
    return {
      service: name,
      status: res.ok ? "operational" : "degraded",
      latencyMs: latency,
      details: `HTTP ${res.status}`,
    };
  } catch (err: any) {
    return {
      service: name,
      status: "down",
      latencyMs: Date.now() - start,
      details: err.message || "Unreachable",
    };
  }
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json",
      ...corsHeaders(),
    },
  });
}

function corsHeaders(): Record<string, string> {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-AEGENTIX-Edge",
  };
}
