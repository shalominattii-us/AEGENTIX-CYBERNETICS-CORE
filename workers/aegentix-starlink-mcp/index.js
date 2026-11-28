/**
 * AEGENTIX Starlink Unified MCP Server (aegentix-starlink-mcp)
 *
 * Hosts:
 * - starlink-edge.aegentixcybernetics.com → edge mesh MCP tools + AAS catalog tools
 * - starlink-mcp.aegentixcybernetics.com  → federates the ROG Ally starlink-mini-mcp
 *   origin (Cloudflare Tunnel) and injects AAS catalog tools into tools/list + tools/call
 *
 * AAS catalog is read-only over public GitHub raw (agentic-awesome-skills main).
 */
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type,Authorization,CF-Access-Client-Id,CF-Access-Client-Secret",
};

const AAS_REPO = "shalominattii-us/agentic-awesome-skills";
const AAS_REF = "main";
const AAS_INDEX_URL = `https://raw.githubusercontent.com/${AAS_REPO}/${AAS_REF}/skills_index.json`;
const AAS_CACHE_TTL_MS = 15 * 60 * 1000;
const AAS_MAX_SKILL_CHARS = 48_000;
const AAS_MAX_FILE_CHARS = 32_000;

const EDGE_TOOLS = [
  {
    name: "mesh_posture",
    description: "Returns live posture across all Cloudflare Service Bindings via jarvis-central-avatar.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "autonomy_status",
    description: "Returns 24/7 autonomous cron schedules, latest XRPL audit snapshot, and RC73XA XDNA 2 NPU attestation.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "railway_cloud_sync",
    description: "Queries Railway aegentix-sovereign-cloud PostgreSQL telemetry history.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "solana_sbt_verify",
    description: "Verifies a Solana Devnet Token-2022 Soulbound or Flywheel credential via aegentix-solana-sbt-devnet.",
    inputSchema: {
      type: "object",
      properties: { wallet: { type: "string" }, mint: { type: "string" } },
      required: ["wallet"],
    },
  },
  {
    name: "r2_vault_status",
    description: "Inspects Cloudflare R2 vaults (world-monitor-treasury-vault & space-bunny-alpha).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "starlink_link_status",
    description: "Returns live edge ASN/Starlink detection (AS14593), edge PoP, and latest Starlink dish telemetry from R2.",
    inputSchema: { type: "object", properties: {} },
  },
];

const AAS_TOOLS = [
  {
    name: "aas_catalog_status",
    description:
      "Agentic Awesome Skills (AAS) catalog status for this Starlink MCP node: index URL, skill count, cache age, and digest.",
    inputSchema: { type: "object", properties: {} },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
  },
  {
    name: "aas_search_skills",
    description:
      "Search the AAS catalog by substring across id, name, description, category, and risk. Returns stable catalog order without relevance scores. Paginate with cursor/limit. Focus one project capability at a time.",
    inputSchema: {
      type: "object",
      properties: {
        query: { type: "string", description: "Case-insensitive substring filter. Empty returns a page of the full catalog." },
        cursor: { type: "integer", minimum: 0, description: "0-based offset into filtered results." },
        limit: { type: "integer", minimum: 1, maximum: 50, description: "Page size (max 50)." },
      },
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
  },
  {
    name: "aas_get_skill",
    description:
      "Fetch one AAS skill by exact id, including frontmatter summary fields and the full SKILL.md body. Compare multiple plausible candidates before composing a stack.",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "string", description: "Exact skill id from the catalog (e.g. cloudflare-workers)." },
      },
      required: ["id"],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
  },
  {
    name: "aas_list_skill_files",
    description: "List tracked files under one AAS skill directory (SKILL.md plus bundled references/scripts when present in the public index path).",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "string", description: "Exact skill id." },
      },
      required: ["id"],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
  },
  {
    name: "aas_read_skill_file",
    description: "Read one file from an AAS skill tree by relative path (e.g. SKILL.md or references/guide.md).",
    inputSchema: {
      type: "object",
      properties: {
        id: { type: "string" },
        path: { type: "string", description: "Relative path inside the skill directory." },
      },
      required: ["id", "path"],
    },
    annotations: { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: true },
  },
];

const AAS_TOOL_NAMES = new Set(AAS_TOOLS.map((t) => t.name));

/** @type {{ fetchedAt: number, skills: any[], digest: string } | null} */
let catalogCache = null;

function jsonResponse(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", ...CORS, ...extraHeaders },
  });
}

function mcpResult(id, result) {
  return jsonResponse({ jsonrpc: "2.0", id: id ?? null, result });
}

function mcpError(id, code, message, status = 400) {
  return jsonResponse({ jsonrpc: "2.0", id: id ?? null, error: { code, message } }, status);
}

function textToolResult(id, out) {
  return mcpResult(id, { content: [{ type: "text", text: typeof out === "string" ? out : JSON.stringify(out) }] });
}

async function sha256Hex(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function loadCatalog() {
  const now = Date.now();
  if (catalogCache && now - catalogCache.fetchedAt < AAS_CACHE_TTL_MS) {
    return catalogCache;
  }
  const res = await fetch(AAS_INDEX_URL, {
    headers: { Accept: "application/json", "User-Agent": "aegentix-starlink-mcp-aas/1.1" },
  });
  if (!res.ok) {
    throw new Error(`AAS index fetch failed: HTTP ${res.status}`);
  }
  const raw = await res.text();
  const skills = JSON.parse(raw);
  if (!Array.isArray(skills)) {
    throw new Error("AAS index is not an array");
  }
  const digest = "sha256-" + (await sha256Hex(raw));
  catalogCache = { fetchedAt: now, skills, digest, count: skills.length };
  return catalogCache;
}

function findSkillMeta(skills, id) {
  const needle = String(id || "").trim();
  return skills.find((s) => s && s.id === needle) || null;
}

function skillRawBase(meta) {
  const rel = String(meta.path || `skills/${meta.id}`).replace(/^\/+/, "");
  return `https://raw.githubusercontent.com/${AAS_REPO}/${AAS_REF}/${rel}`;
}

function skillApiContentsUrl(meta) {
  const rel = String(meta.path || `skills/${meta.id}`).replace(/^\/+/, "");
  return `https://api.github.com/repos/${AAS_REPO}/contents/${rel}?ref=${AAS_REF}`;
}

function safeRelPath(path) {
  const p = String(path || "").replace(/\\/g, "/").replace(/^\/+/, "");
  if (!p || p.includes("..") || p.includes("\0")) return null;
  return p;
}

async function runAasTool(name, args) {
  const catalog = await loadCatalog();
  if (name === "aas_catalog_status") {
    return {
      ok: true,
      service: "aegentix-starlink-mcp",
      aas: {
        package: "agentic-awesome-skills",
        repo: AAS_REPO,
        ref: AAS_REF,
        indexUrl: AAS_INDEX_URL,
        skillCount: catalog.count,
        digest: catalog.digest,
        cacheAgeMs: Date.now() - catalog.fetchedAt,
        tools: [...AAS_TOOL_NAMES],
        mode: "read-only-catalog",
      },
      ts: new Date().toISOString(),
    };
  }
  if (name === "aas_search_skills") {
    const q = String(args.query || "").trim().toLowerCase();
    const cursor = Math.max(0, Number.parseInt(String(args.cursor ?? "0"), 10) || 0);
    const limit = Math.min(50, Math.max(1, Number.parseInt(String(args.limit ?? "20"), 10) || 20));
    const filtered = !q
      ? catalog.skills
      : catalog.skills.filter((s) => {
          const hay = [s.id, s.name, s.description, s.category, s.risk, s.source]
            .filter(Boolean)
            .join("\n")
            .toLowerCase();
          return hay.includes(q);
        });
    const page = filtered.slice(cursor, cursor + limit).map((s) => ({
      id: s.id,
      name: s.name,
      category: s.category,
      description: s.description,
      risk: s.risk,
      source: s.source,
      path: s.path,
      date_added: s.date_added,
    }));
    const nextCursor = cursor + limit < filtered.length ? cursor + limit : null;
    return {
      ok: true,
      query: q,
      total: filtered.length,
      cursor,
      limit,
      nextCursor,
      catalogDigest: catalog.digest,
      skills: page,
    };
  }
  if (name === "aas_get_skill") {
    const meta = findSkillMeta(catalog.skills, args.id);
    if (!meta) {
      throw new Error(`Unknown skill id: ${String(args.id || "")}`);
    }
    const url = `${skillRawBase(meta)}/SKILL.md`;
    const res = await fetch(url, { headers: { "User-Agent": "aegentix-starlink-mcp-aas/1.1" } });
    if (!res.ok) {
      throw new Error(`SKILL.md fetch failed for ${meta.id}: HTTP ${res.status}`);
    }
    let body = await res.text();
    let truncated = false;
    if (body.length > AAS_MAX_SKILL_CHARS) {
      body = body.slice(0, AAS_MAX_SKILL_CHARS);
      truncated = true;
    }
    return {
      ok: true,
      skill: meta,
      skillMdUrl: url,
      truncated,
      content: body,
      catalogDigest: catalog.digest,
    };
  }
  if (name === "aas_list_skill_files") {
    const meta = findSkillMeta(catalog.skills, args.id);
    if (!meta) {
      throw new Error(`Unknown skill id: ${String(args.id || "")}`);
    }
    const res = await fetch(skillApiContentsUrl(meta), {
      headers: {
        Accept: "application/vnd.github+json",
        "User-Agent": "aegentix-starlink-mcp-aas/1.1",
      },
    });
    if (!res.ok) {
      // Fallback: at least SKILL.md is known to exist for catalog entries.
      return {
        ok: true,
        id: meta.id,
        path: meta.path,
        files: [{ path: "SKILL.md", type: "file", note: "github_api_unavailable_fallback" }],
        httpStatus: res.status,
      };
    }
    const entries = await res.json();
    const files = Array.isArray(entries)
      ? entries.map((e) => ({ path: e.name, type: e.type, size: e.size }))
      : [{ path: "SKILL.md", type: "file" }];
    return { ok: true, id: meta.id, path: meta.path, files };
  }
  if (name === "aas_read_skill_file") {
    const meta = findSkillMeta(catalog.skills, args.id);
    if (!meta) {
      throw new Error(`Unknown skill id: ${String(args.id || "")}`);
    }
    const rel = safeRelPath(args.path);
    if (!rel) {
      throw new Error("Invalid path");
    }
    const url = `${skillRawBase(meta)}/${rel}`;
    const res = await fetch(url, { headers: { "User-Agent": "aegentix-starlink-mcp-aas/1.1" } });
    if (!res.ok) {
      throw new Error(`File fetch failed: HTTP ${res.status}`);
    }
    let body = await res.text();
    let truncated = false;
    if (body.length > AAS_MAX_FILE_CHARS) {
      body = body.slice(0, AAS_MAX_FILE_CHARS);
      truncated = true;
    }
    return { ok: true, id: meta.id, path: rel, truncated, content: body };
  }
  throw new Error("Unknown AAS tool: " + name);
}

async function runEdgeTool(name, args, env, request) {
  if (name === "mesh_posture") {
    const r = await env.SVC_JARVIS.fetch("https://internal/api/posture");
    return await r.json();
  }
  if (name === "autonomy_status") {
    const r = await env.SVC_JARVIS.fetch("https://internal/api/autonomy");
    return await r.json();
  }
  if (name === "railway_cloud_sync") {
    const r = await fetch("https://aegentix-sovereign-gateway-production.up.railway.app/api/history");
    return await r.json();
  }
  if (name === "solana_sbt_verify") {
    const w = encodeURIComponent(String(args.wallet || ""));
    const m = args.mint ? "&mint=" + encodeURIComponent(String(args.mint)) : "";
    const r = await env.SVC_SOLANA_SBT.fetch("https://internal/api/verify?wallet=" + w + m);
    return await r.json();
  }
  if (name === "r2_vault_status") {
    const [treasuryList, assetsList] = await Promise.all([
      env.TREASURY_VAULT ? env.TREASURY_VAULT.list({ limit: 25 }) : { objects: [] },
      env.AEGENTIX_ASSETS ? env.AEGENTIX_ASSETS.list({ limit: 25 }) : { objects: [] },
    ]);
    return {
      ok: true,
      treasury_vault: {
        bucket: "world-monitor-treasury-vault",
        sample_count: treasuryList.objects.length,
        truncated: Boolean(treasuryList.truncated),
        latest_keys: treasuryList.objects.slice(-5).map((o) => o.key),
      },
      aegentix_assets: {
        bucket: "space-bunny-alpha",
        sample_count: assetsList.objects.length,
        truncated: Boolean(assetsList.truncated),
        latest_keys: assetsList.objects.slice(-5).map((o) => o.key),
      },
      ts: new Date().toISOString(),
    };
  }
  if (name === "starlink_link_status") {
    const cf = request.cf || {};
    let dish = null;
    if (env.TREASURY_VAULT) {
      const obj = await env.TREASURY_VAULT.get("starlink-mcp/latest-dish-telemetry.json");
      if (obj) dish = await obj.json();
    }
    const isStarlink = Number(cf.asn) === 14593 || /starlink|spacex/i.test(String(cf.asOrganization || ""));
    return {
      ok: true,
      edge_colo: cf.colo || "UNKNOWN",
      client_asn: cf.asn || null,
      client_isp: cf.asOrganization || null,
      starlink_uplink_detected: isStarlink,
      dish_telemetry_endpoint: "POST /api/starlink/telemetry (expects gRPC bridge payload from 192.168.100.1:9200)",
      latest_dish_telemetry: dish || { status: "READY_AWAITING_DISH_TELEMETRY" },
      ts: new Date().toISOString(),
    };
  }
  throw new Error("Unknown tool: " + name);
}

function isStarlinkMiniHost(hostname) {
  return hostname === "starlink-mcp.aegentixcybernetics.com";
}

function isMcpPostPath(pathname) {
  return pathname === "/mcp" || pathname === "/mcp/starlink" || pathname === "/";
}

async function handleEdgeMcp(req, env, request) {
  if (req.method === "initialize") {
    return mcpResult(req.id, {
      protocolVersion: "2024-11-05",
      serverInfo: { name: "aegentix-starlink-mcp", version: "1.1.0-aas" },
      capabilities: { tools: {} },
    });
  }
  if (req.method === "tools/list") {
    return mcpResult(req.id, { tools: [...EDGE_TOOLS, ...AAS_TOOLS] });
  }
  if (req.method === "tools/call") {
    const toolName = String(req.params?.name || "");
    const toolArgs = req.params?.arguments || {};
    try {
      const out = AAS_TOOL_NAMES.has(toolName)
        ? await runAasTool(toolName, toolArgs)
        : await runEdgeTool(toolName, toolArgs, env, request);
      return textToolResult(req.id, out);
    } catch (err) {
      return mcpError(req.id, -32603, err instanceof Error ? err.message : String(err));
    }
  }
  return mcpError(req.id, -32601, "Method not found", 404);
}

async function handleFederatedMiniMcp(req, request) {
  const toolName = String(req.params?.name || "");

  if (req.method === "tools/call" && AAS_TOOL_NAMES.has(toolName)) {
    try {
      const out = await runAasTool(toolName, req.params?.arguments || {});
      return textToolResult(req.id, out);
    } catch (err) {
      return mcpError(req.id, -32603, err instanceof Error ? err.message : String(err));
    }
  }

  if (req.method === "tools/list") {
    const originRes = await fetch(request);
    const originText = await originRes.text();
    let originJson;
    try {
      originJson = JSON.parse(originText);
    } catch {
      return new Response(originText, {
        status: originRes.status,
        headers: { ...Object.fromEntries(originRes.headers), ...CORS },
      });
    }
    const originTools = originJson?.result?.tools;
    if (!Array.isArray(originTools)) {
      return jsonResponse(originJson, originRes.status);
    }
    const existing = new Set(originTools.map((t) => t?.name).filter(Boolean));
    const injected = AAS_TOOLS.filter((t) => !existing.has(t.name));
    return jsonResponse(
      {
        ...originJson,
        result: {
          ...originJson.result,
          tools: [...originTools, ...injected],
          _meta: {
            ...(originJson.result._meta || {}),
            aasFederation: {
              injected: injected.map((t) => t.name),
              catalog: AAS_REPO + "@" + AAS_REF,
            },
          },
        },
      },
      originRes.status,
    );
  }

  // initialize and all other methods: pass through to ROG Ally origin via tunnel
  return fetch(request);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: CORS });

    const miniHost = isStarlinkMiniHost(url.hostname);

    // Federation host: health stays origin-native except we advertise AAS on /health enrichment via Worker when path is exact.
    if (miniHost) {
      if (request.method === "POST" && isMcpPostPath(url.pathname)) {
        let req;
        try {
          req = await request.clone().json();
        } catch {
          return fetch(request);
        }
        // Only intercept JSON-RPC methods we federate; always keep a clone for origin proxy.
        if (req && (req.method === "tools/list" || (req.method === "tools/call" && AAS_TOOL_NAMES.has(String(req.params?.name || ""))))) {
          return handleFederatedMiniMcp(req, request);
        }
        return fetch(request);
      }
      return fetch(request);
    }

    // Edge host (starlink-edge / workers.dev)
    if (request.method === "GET" && (url.pathname === "/" || url.pathname === "/health")) {
      const cf = request.cf || {};
      let aas = null;
      try {
        const catalog = await loadCatalog();
        aas = { skillCount: catalog.count, digest: catalog.digest, tools: [...AAS_TOOL_NAMES] };
      } catch (err) {
        aas = { error: err instanceof Error ? err.message : String(err) };
      }
      return jsonResponse({
        ok: true,
        service: "aegentix-starlink-mcp",
        version: "1.1.0-aas",
        protocol: "MCP JSON-RPC 2.0 (POST /mcp)",
        edge_colo: cf.colo || "UNKNOWN",
        starlink_uplink_detected:
          Number(cf.asn) === 14593 || /starlink|spacex/i.test(String(cf.asOrganization || "")),
        connected_services: [
          "jarvis-central-avatar (Service Binding)",
          "aegentix-treasury-labs-mcp (Service Binding)",
          "aegentix-solana-sbt-devnet (Service Binding)",
          "aegentix-edge (Service Binding)",
          "bold-bit-champions-cup (Service Binding)",
          "railway: aegentix-sovereign-gateway + Postgres + Redis + Qdrant",
          "r2: world-monitor-treasury-vault + space-bunny-alpha (AEGENTIX_ASSETS)",
          "aas: agentic-awesome-skills catalog (GitHub raw)",
        ],
        tools: [...EDGE_TOOLS.map((t) => t.name), ...AAS_TOOLS.map((t) => t.name)],
        aas,
        ts: new Date().toISOString(),
      });
    }

    if (request.method === "POST" && url.pathname === "/api/starlink/telemetry") {
      if (env.STARLINK_TELEMETRY_TOKEN) {
        const auth = request.headers.get("authorization") || "";
        if (auth !== "Bearer " + env.STARLINK_TELEMETRY_TOKEN) {
          return jsonResponse({ ok: false, error: "Unauthorized" }, 401);
        }
      }
      const body = await request.json();
      const rec = { ...body, received_utc: new Date().toISOString() };
      if (env.TREASURY_VAULT) {
        await env.TREASURY_VAULT.put("starlink-mcp/latest-dish-telemetry.json", JSON.stringify(rec), {
          httpMetadata: { contentType: "application/json" },
        });
      }
      return jsonResponse({ ok: true, status: "STARLINK_TELEMETRY_STORED", rec });
    }

    if (request.method === "POST" && (url.pathname === "/mcp" || url.pathname === "/mcp/starlink")) {
      const req = await request.json();
      return handleEdgeMcp(req, env, request);
    }

    return jsonResponse(
      { error: "Not Found", endpoints: ["GET /health", "POST /mcp", "POST /api/starlink/telemetry"] },
      404,
    );
  },
};
