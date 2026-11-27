import { SELF } from "cloudflare:test";
import { describe, expect, it } from "vitest";

describe("worker integration", () => {
  it("serves the home page over http without HSTS", async () => {
    const response = await SELF.fetch("http://example.com/");
    expect(response.status).toBe(200);
    expect(response.headers.get("content-type")).toContain("text/html");
    expect(response.headers.get("content-security-policy")).toContain("default-src 'self'");
    expect(response.headers.get("strict-transport-security")).toBeNull();
    expect(await response.text()).toContain("From a solicitation sentence to a closed gate.");
  });

  it("sends HSTS for https pages and the sample snapshot", async () => {
    const page = await SELF.fetch("https://example.com/boundary/");
    expect(page.status).toBe(200);
    expect(page.headers.get("strict-transport-security")).toContain("max-age=31536000");
    expect(page.headers.get("content-security-policy")).toContain("upgrade-insecure-requests");
    const snapshot = await SELF.fetch("https://example.com/api/opportunities");
    expect(snapshot.status).toBe(200);
    const body = await snapshot.json() as { fictional: boolean; label: string; records: Array<{ issuer: string }> };
    expect(body.fictional).toBe(true);
    expect(body.label).toBe("SAMPLE DATA");
    expect(body.records.every((record) => /fictional/i.test(record.issuer))).toBe(true);
  });

  it("runs the demo and then rate limits that client", async () => {
    const headers = { "content-type": "application/json", "cf-connecting-ip": "203.0.113.50" };
    const first = await SELF.fetch("https://example.com/api/demo/analyze", {
      method: "POST",
      headers,
      body: JSON.stringify({ sampleId: "water", authorizationToken: "AEGENTIX-AUTH-should-not-echo" }),
    });
    expect(first.status).toBe(200);
    const body = await first.json() as {
      plan: { externalActionsBlocked: boolean; tasks: Array<{ id: string }> };
      gate: { tokenAccepted: boolean };
      specification: { approvalState: string };
    };
    expect(body.plan.externalActionsBlocked).toBe(true);
    expect(body.plan.tasks.map((task) => task.id)).toEqual(["TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-005"]);
    expect(body.specification.approvalState).toBe("draft");
    expect(body.gate.tokenAccepted).toBe(false);
    expect(JSON.stringify(body)).not.toContain("should-not-echo");

    let limited = false;
    for (let attempt = 0; attempt < 24; attempt += 1) {
      const response = await SELF.fetch("https://example.com/api/demo/analyze", {
        method: "POST",
        headers,
        body: JSON.stringify({ sampleId: "quiet" }),
      });
      if (response.status === 429) {
        limited = true;
        expect(response.headers.get("retry-after")).toBe("60");
        break;
      }
    }
    expect(limited).toBe(true);
  });

  it("does not expose an ingest or admin route", async () => {
    const ingest = await SELF.fetch("https://example.com/api/opportunities/ingest", { method: "POST", body: "{}" });
    expect(ingest.status).toBe(404);
    const health = await SELF.fetch("https://example.com/api/health");
    const body = await health.json() as { mode: string; reads: string };
    expect(body.mode).toBe("public-read-only");
    expect(body.reads).toBe("static-snapshot-and-sample-text");
  });
});
