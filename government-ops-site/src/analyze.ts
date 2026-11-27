import {
  assertExternalActionAuthorized,
  runInternalPipeline,
} from "../../government-ops-spine/src/pipeline.js";
import type { OpportunityType, PublicOpportunity } from "../../government-ops-spine/src/types.js";
import { DEMO_SAMPLES, SAMPLE_CAPABILITIES, findSample, type DemoSample } from "./samples.js";

const BLOCKED_ACTIONS = ["submit_offer", "file_patent", "commit_funds", "external_representation"] as const;
const RETRIEVED_AT = "1970-01-01T00:00:00Z";
const PROVENANCE_URL = "urn:sample:government-ops-site:demo";

export interface DemoAnalysis {
  label: "SAMPLE DEMO";
  disclaimer: string;
  source: "sample" | "pasted-text";
  sampleId?: string;
  wrapper: {
    label: "DEMO WRAPPER";
    note: string;
    opportunityType: OpportunityType;
    issuer: string;
    provenanceAuthority: "aggregator";
    provenanceUrl: string;
  };
  capabilityCatalog: {
    label: "SAMPLE CAPABILITY CATALOG";
    disclaimer: string;
    records: Array<Pick<(typeof SAMPLE_CAPABILITIES)[number], "id" | "name" | "tags" | "maturity">>;
  };
  analysis: ReturnType<typeof runInternalPipeline>["analysis"];
  specification: ReturnType<typeof runInternalPipeline>["specification"];
  matches: ReturnType<typeof runInternalPipeline>["matches"];
  plan: ReturnType<typeof runInternalPipeline>["plan"];
  contentHash: {
    algorithm: "SHA-256";
    hex: string;
    subject: "spine-demo-result-json";
    note: string;
  };
  gate: {
    externalActionsBlocked: true;
    tokenAccepted: false;
    checks: Array<{ action: (typeof BLOCKED_ACTIONS)[number]; blocked: true; message: string }>;
  };
}

export function listSamples(): { label: "SAMPLE DATA"; disclaimer: string; samples: DemoSample[] } {
  return {
    label: "SAMPLE DATA",
    disclaimer: "Fictional solicitation text used only to exercise the public demo. Not a live notice.",
    samples: DEMO_SAMPLES,
  };
}

export async function analyzeDemo(input: { text?: string; sampleId?: string }): Promise<DemoAnalysis> {
  const sample = findSample(input.sampleId);
  const pasted = input.text?.trim() ?? "";
  const text = pasted || sample?.text || "";
  if (!text) {
    throw new Error("Paste solicitation text or choose a sample.");
  }
  const matched = DEMO_SAMPLES.find((item) => item.text === text);
  const source = matched ? "sample" : "pasted-text";
  const externalId = matched ? matched.externalId : `SAMPLE-${(await sha256Hex(text)).slice(0, 8).toUpperCase()}`;
  const opportunity = demoOpportunity({
    externalId,
    title: matched?.title ?? firstLine(text),
    opportunityType: matched?.opportunityType ?? "RFP",
    deadline: matched?.deadline ?? "2026-12-31T17:00:00Z",
    text,
  });
  const spine = runInternalPipeline(opportunity, SAMPLE_CAPABILITIES);
  const canonical = JSON.stringify({
    analysis: spine.analysis,
    specification: spine.specification,
    matches: spine.matches,
    plan: spine.plan,
  });
  return {
    label: "SAMPLE DEMO",
    disclaimer:
      "Computed in this Worker from the pasted or selected sample and a fictional capability catalog. Nothing was stored, and no internal system was contacted.",
    source,
    sampleId: matched?.id,
    wrapper: {
      label: "DEMO WRAPPER",
      note: "These fields exist so the spine parser has a complete record. They are not facts extracted from an agency system.",
      opportunityType: opportunity.opportunityType,
      issuer: opportunity.issuer,
      provenanceAuthority: "aggregator",
      provenanceUrl: PROVENANCE_URL,
    },
    capabilityCatalog: {
      label: "SAMPLE CAPABILITY CATALOG",
      disclaimer:
        "Fictional tags used to exercise matchCapabilities. Not the live capability index, and not evidence of delivery or past performance.",
      records: SAMPLE_CAPABILITIES.map(({ id, name, tags, maturity }) => ({ id, name, tags, maturity })),
    },
    analysis: spine.analysis,
    specification: spine.specification,
    matches: spine.matches,
    plan: spine.plan,
    contentHash: {
      algorithm: "SHA-256",
      hex: await sha256Hex(canonical),
      subject: "spine-demo-result-json",
      note: "SHA-256 of the demo's analysis, specification, matches, and plan JSON. The spine's PDF and DOCX renderer hashes file bytes the same way and is not invoked here.",
    },
    gate: closedGate(),
  };
}

export function demoOpportunity(input: {
  externalId: string;
  title: string;
  opportunityType: OpportunityType;
  deadline: string;
  text: string;
}): PublicOpportunity {
  return {
    schemaVersion: "1.0.0",
    eventId: `demo:${input.externalId}`,
    externalId: input.externalId,
    title: input.title.slice(0, 180),
    issuer: "Public demo input (fictional)",
    jurisdiction: "SAMPLE",
    opportunityType: input.opportunityType,
    deadline: input.deadline,
    eligibility: [],
    requiredRegistrations: [],
    summary: "Fictional sample wrapped for the public demo parser.",
    rawText: input.text,
    provenance: [
      {
        system: "public-demo",
        authority: "aggregator",
        url: PROVENANCE_URL,
        retrievedAt: RETRIEVED_AT,
      },
    ],
  };
}

function closedGate(): DemoAnalysis["gate"] {
  const checks = BLOCKED_ACTIONS.map((action) => {
    try {
      assertExternalActionAuthorized(action);
    } catch (error) {
      const message = error instanceof Error ? error.message : "blocked";
      return { action, blocked: true as const, message };
    }
    throw new Error(`Authorization gate failed open for ${action}.`);
  });
  return { externalActionsBlocked: true, tokenAccepted: false, checks };
}

function firstLine(text: string): string {
  const line = text.split(/\n+/).map((part) => part.trim()).find(Boolean);
  return line && line.length >= 12 ? line.slice(0, 180) : "Pasted sample solicitation";
}

export async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}
