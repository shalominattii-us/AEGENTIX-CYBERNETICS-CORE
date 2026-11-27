import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { beforeEach, describe, expect, it } from "vitest";
import { resetDemoLimiter } from "../../src/limiter.js";
import { route, type SiteDeps } from "../../src/route.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const snapshot = readFileSync(path.join(root, "public/snapshot/opportunities.json"), "utf8");

function deps(overrides: Partial<SiteDeps> = {}): SiteDeps & { calls: string[] } {
  const calls: string[] = [];
  return {
    calls,
    siteMode: "public-read-only",
    now: () => 1_700_000_000_000,
    limitDemo: async () => true,
    fetchAsset: async (request) => {
      const pathname = new URL(request.url).pathname;
      calls.push(pathname);
      if (pathname === "/snapshot/opportunities.json") {
        return new Response(snapshot, { headers: { "content-type": "application/json" } });
      }
      if (pathname === "/404.html") return new Response("<html>missing</html>", { status: 200, headers: { "content-type": "text/html" } });
      if (pathname === "/") return new Response("<html>home</html>", { status: 200, headers: { "content-type": "text/html" } });
      return new Response("missing", { status: 404 });
    },
    ...overrides,
  };
}

describe("public routes", () => {
  beforeEach(() => resetDemoLimiter());

  it("serves pages with security headers and no HSTS on http", async () => {
    const response = await route(new Request("http://example.test/"), deps());
    expect(response.status).toBe(200);
    expect(response.headers.get("content-security-policy")).toContain("default-src 'self'");
    expect(response.headers.get("content-security-policy")).not.toContain("upgrade-insecure-requests");
    expect(response.headers.get("strict-transport-security")).toBeNull();
    expect(response.headers.get("x-content-type-options")).toBe("nosniff");
    expect(response.headers.get("x-frame-options")).toBe("DENY");
    expect(response.headers.get("referrer-policy")).toBe("no-referrer");
  });

  it("adds HSTS on https", async () => {
    const response = await route(new Request("https://example.test/boundary/"), deps({
      fetchAsset: async () => new Response("<html>boundary</html>", { status: 200, headers: { "content-type": "text/html" } }),
    }));
    expect(response.headers.get("strict-transport-security")).toContain("max-age=31536000");
    expect(response.headers.get("content-security-policy")).toContain("upgrade-insecure-requests");
  });

  it("analyzes a sample, ignores an authorization token, and blocks external actions", async () => {
    const bridge = deps();
    const response = await route(new Request("https://example.test/api/demo/analyze", {
      method: "POST",
      headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.8" },
      body: JSON.stringify({ sampleId: "water", authorizationToken: "AEGENTIX-AUTH-should-not-echo" }),
    }), bridge);
    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.plan.externalActionsBlocked).toBe(true);
    expect(body.gate.tokenAccepted).toBe(false);
    expect(JSON.stringify(body)).not.toContain("should-not-echo");
    expect(body.specification.approvalState).toBe("draft");
    expect(bridge.calls).toEqual([]);
  });

  it("rejects an empty demo body and an oversized body", async () => {
    const empty = await route(new Request("https://example.test/api/demo/analyze", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({}),
    }), deps());
    expect(empty.status).toBe(400);
    const huge = await route(new Request("https://example.test/api/demo/analyze", {
      method: "POST",
      headers: { "content-type": "application/json", "content-length": "999999" },
      body: JSON.stringify({ text: "short" }),
    }), deps());
    expect(huge.status).toBe(413);
  });

  it("rate limits the demo and fails closed when the binding throws", async () => {
    const limited = deps();
    let status = 0;
    for (let attempt = 0; attempt < 25; attempt += 1) {
      const response = await route(new Request("https://example.test/api/demo/analyze", {
        method: "POST",
        headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.21" },
        body: JSON.stringify({ sampleId: "quiet" }),
      }), limited);
      status = response.status;
      if (status === 429) break;
    }
    expect(status).toBe(429);
    resetDemoLimiter();
    const unavailable = await route(new Request("https://example.test/api/demo/analyze", {
      method: "POST",
      headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.22" },
      body: JSON.stringify({ sampleId: "quiet" }),
    }), deps({ limitDemo: async () => { throw new Error("binding down"); } }));
    expect(unavailable.status).toBe(503);
  });

  it("returns the fictional snapshot and one record, and hides ingest", async () => {
    const bridge = deps();
    const list = await route(new Request("https://example.test/api/opportunities"), bridge);
    expect(list.status).toBe(200);
    const body = await list.json();
    expect(body.fictional).toBe(true);
    expect(body.label).toBe("SAMPLE DATA");
    expect(body.externalActionsBlocked).toBe(true);
    expect(body.records.map((record: { id: string }) => record.id)).toContain("SAMPLE-WATER");
    expect(JSON.stringify(body)).not.toMatch(/@/);
    expect(bridge.calls).toEqual(["/snapshot/opportunities.json"]);
    const one = await route(new Request("https://example.test/api/opportunities/SAMPLE-CANCELLED"), deps());
    expect(one.status).toBe(200);
    const ingest = await route(new Request("https://example.test/api/opportunities/ingest", { method: "POST", body: "{}" }), deps());
    expect(ingest.status).toBe(404);
    const admin = await route(new Request("https://example.test/api/admin"), deps());
    expect(admin.status).toBe(404);
  });

  it("falls back to the 404 page for unknown assets", async () => {
    const response = await route(new Request("https://example.test/missing-page"), deps());
    expect(response.status).toBe(404);
    expect(await response.text()).toContain("missing");
  });
});
