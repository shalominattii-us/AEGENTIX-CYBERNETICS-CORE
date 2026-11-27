import { readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { DEMO_LIMIT, DEMO_WINDOW_MS } from "../../src/limiter.js";
import { validateSnapshot } from "../../src/snapshot.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

function stripJsonc(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|\s)\/\/.*$/gm, "$1");
}

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) return walk(full);
    return full;
  });
}

describe("public boundary", () => {
  it("ships a validator-clean fictional snapshot", () => {
    const snapshot = validateSnapshot(JSON.parse(readFileSync(path.join(root, "public/snapshot/opportunities.json"), "utf8")));
    expect(snapshot.records.length).toBeGreaterThanOrEqual(6);
    expect(snapshot.records.every((record) => /fictional/i.test(record.issuer))).toBe(true);
    expect(snapshot.records.every((record) => record.setAside === null)).toBe(true);
    expect(snapshot.records.map((record) => record.status)).toEqual(expect.arrayContaining(["sample-open", "sample-closed", "sample-cancelled"]));
  });

  it("keeps wrangler free of internal bindings and aligned with the demo limit", () => {
    const config = JSON.parse(stripJsonc(readFileSync(path.join(root, "wrangler.jsonc"), "utf8"))) as Record<string, unknown>;
    for (const key of ["kv_namespaces", "r2_buckets", "d1_databases", "services", "hyperdrive", "routes", "vars_secrets"]) {
      expect(config[key], key).toBeUndefined();
    }
    expect(config.ratelimits).toEqual([
      expect.objectContaining({ name: "DEMO_RATE_LIMITER", simple: { limit: DEMO_LIMIT, period: DEMO_WINDOW_MS / 1000 } }),
    ]);
    expect(JSON.stringify(config)).not.toMatch(/api[_-]?key|secret|password|DATABASE_URL|postgres/i);
    const observability = config.observability as { enabled: boolean; logs: { enabled: boolean }; traces: { enabled: boolean } };
    expect(observability.enabled).toBe(true);
    expect(observability.logs.enabled).toBe(true);
    expect(observability.traces.enabled).toBe(true);
  });

  it("labels every page and describes keyless public intake without registration claims", () => {
    const pages = walk(path.join(root, "public")).filter((file) => file.endsWith(".html"));
    const denial = "This organization has no verified SAM.gov registration, UEI, CAGE code, FedRAMP authorization, ATO, certification, past performance, or named personnel on this site.";
    expect(pages.length).toBeGreaterThanOrEqual(5);
    for (const file of pages) {
      const html = readFileSync(file, "utf8");
      expect(html, file).toContain("Public read-only. Sample data only. No path into internal systems.");
      expect(html, file).toContain(denial);
      expect(html, file).toContain('href="/demo/"');
      expect(html, file).toContain('href="/opportunities/"');
      expect(html, file).toContain('href="/boundary/"');
      expect(html, file).not.toMatch(/we are fedramp|our uei|our cage|registered in sam|authority to operate|certified iso/i);
    }
    const home = readFileSync(path.join(root, "public/index.html"), "utf8");
    expect(home).toContain("parseOpportunity");
    expect(home).toContain("TASK-001");
    expect(home).toContain("externalActionsBlocked");
    expect(home).toContain("SHA-256");
    expect(home).toContain("public Contract Opportunities CSV extract");
    expect(home).toContain("Grants.gov");
    expect(home).toContain("does not depend on a SAM.gov API key");
    expect(home).not.toMatch(/requires an API key/i);
  });
});
