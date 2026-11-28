import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { runInternalPipeline } from "../../../government-ops-spine/src/pipeline.js";
import { analyzeDemo, demoOpportunity, sha256Hex } from "../../src/analyze.js";
import { DEMO_SAMPLES, SAMPLE_CAPABILITIES } from "../../src/samples.js";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

describe("demo analysis", () => {
  it("matches the spine pipeline and shows mandatory, optional, and all match dispositions", async () => {
    const result = await analyzeDemo({ sampleId: "water" });
    const opportunity = demoOpportunity({
      externalId: "SAMPLE-WATER",
      title: "Water-network sensor prototype (sample)",
      opportunityType: "RFP",
      deadline: "2026-12-18T17:00:00-05:00",
      text: DEMO_SAMPLES[0].text,
    });
    const direct = runInternalPipeline(opportunity, SAMPLE_CAPABILITIES);
    expect(result.analysis).toEqual(direct.analysis);
    expect(result.specification).toEqual(direct.specification);
    expect(result.matches).toEqual(direct.matches);
    expect(result.plan).toEqual(direct.plan);
    expect(result.analysis.requirements.some((item) => item.mandatory)).toBe(true);
    expect(result.analysis.requirements.some((item) => !item.mandatory)).toBe(true);
    expect(result.analysis.standards.some((line) => /NIST|FAR|DFARS/.test(line))).toBe(true);
    expect(new Set(result.matches.map((match) => match.disposition))).toEqual(new Set(["reuse", "adapt", "build"]));
    expect(result.specification.approvalState).toBe("draft");
    expect(result.plan.externalActionsBlocked).toBe(true);
    expect(result.plan.tasks.map((task) => task.id)).toEqual(["TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-005"]);
    expect(result.plan.tasks.map((task) => task.executionZone)).toEqual(["KERNEL", "TREASURY", "AI", "SECURITY", "XR"]);
    expect(result.gate.tokenAccepted).toBe(false);
    expect(result.gate.checks.map((check) => check.action)).toEqual([
      "submit_offer",
      "file_patent",
      "commit_funds",
      "external_representation",
    ]);
    expect(result.gate.checks.every((check) => check.blocked && check.message.includes("explicit AEGENTIX authorization"))).toBe(true);
    const canonical = JSON.stringify({
      analysis: result.analysis,
      specification: result.specification,
      matches: result.matches,
      plan: result.plan,
    });
    expect(result.contentHash.hex).toBe(await sha256Hex(canonical));
    expect(result.contentHash.algorithm).toBe("SHA-256");
  });

  it("flags review when the sample has no requirement keywords", async () => {
    const result = await analyzeDemo({ sampleId: "quiet" });
    expect(result.analysis.requirements).toEqual([]);
    expect(result.analysis.reviewRequired).toBe(true);
    expect(result.matches).toEqual([]);
    expect(result.plan.tasks).toHaveLength(5);
  });

  it("uses solicitation wording as the specification objective", async () => {
    const result = await analyzeDemo({ sampleId: "water" });
    expect(result.specification.objective).toContain("Northline Municipal Utilities");
    expect(result.specification.objective).not.toBe("Fictional sample wrapped for the public demo parser.");
  });

  it("does not duplicate requirements that already appear in rawText", async () => {
    const text = DEMO_SAMPLES[0].text;
    const opportunity = demoOpportunity({
      externalId: "SAMPLE-WATER",
      title: "Water-network sensor prototype (sample)",
      opportunityType: "RFP",
      deadline: "2026-12-18T17:00:00-05:00",
      text,
    });
    expect(opportunity.summary).not.toMatch(/\b(must|shall|required)\b/i);
    const result = await analyzeDemo({ sampleId: "water" });
    const statements = result.analysis.requirements.map((item) => item.statement);
    expect(new Set(statements).size).toBe(statements.length);
    const rawOnly = runInternalPipeline(
      { ...opportunity, summary: "Northline Municipal Utilities is asking for a planning prototype." },
      SAMPLE_CAPABILITIES,
    );
    expect(result.analysis.requirements).toEqual(rawOnly.analysis.requirements);
    expect(result.matches).toEqual(rawOnly.matches);
  });

  it("does not import storage, mail, or agency clients", () => {
    const banned = [/from\s+["']pg["']/, /postgres/i, /api\.sam\.gov/i, /googleapis/i, /nodemailer/i, /DATABASE_URL/, /\b8099\b/, /child_process/, /gmail/i, /hyperdrive/i];
    for (const file of readdirSync(path.join(root, "src"))) {
      if (!file.endsWith(".ts")) continue;
      const source = readFileSync(path.join(root, "src", file), "utf8");
      for (const pattern of banned) expect(source, file).not.toMatch(pattern);
      expect(source, file).not.toMatch(/fetch\s*\(\s*["'`]/);
    }
    const analyze = readFileSync(path.join(root, "src/analyze.ts"), "utf8");
    expect(analyze).toContain("government-ops-spine/src/pipeline.js");
    expect(analyze).not.toContain("document-rendering");
  });
});
