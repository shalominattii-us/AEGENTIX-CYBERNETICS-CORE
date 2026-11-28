import type { CapabilityRecord } from "../../government-ops-spine/src/types.js";

export interface DemoSample {
  id: string;
  externalId: string;
  title: string;
  blurb: string;
  opportunityType: "RFP" | "SOURCES_SOUGHT" | "FORECAST";
  deadline: string;
  text: string;
}

export const SAMPLE_CAPABILITIES: CapabilityRecord[] = [
  {
    id: "SAMPLE-CAP-SENSOR",
    name: "Sample sensor-ingest note",
    tags: ["sensor", "data"],
    maturity: "sample-only",
    evidence: ["sample-catalog:not-a-delivery-record"],
    executionZones: ["SAMPLE"],
  },
  {
    id: "SAMPLE-CAP-TWIN",
    name: "Sample digital-twin sketch",
    tags: ["digital", "twin", "sensor"],
    maturity: "sample-only",
    evidence: ["sample-catalog:not-a-delivery-record"],
    executionZones: ["SAMPLE"],
  },
  {
    id: "SAMPLE-CAP-LOGISTICS",
    name: "Sample logistics checklist",
    tags: ["logistics", "schedule"],
    maturity: "sample-only",
    evidence: ["sample-catalog:not-a-delivery-record"],
    executionZones: ["SAMPLE"],
  },
];

const water = `Northline Municipal Utilities (fictional sample, not a live notice) is asking for a planning prototype.
The system shall ingest sensor data through a documented interface.
The prototype must include a digital twin for planning reviews.
Vendors must demonstrate cybersecurity compliance with the published control baseline.
The contractor shall deliver architecture documentation and a working prototype on the stated schedule.
Work shall comply with NIST SP 800-53 control families and the applicable FAR and DFARS clauses where a real solicitation would cite them.
The offeror is eligible to deliver an optional training session if capable of supporting operators.
The objective is to improve capital planning for the water network.`;

const port = `Harborline Port Authority (fictional sample, not a live notice) is collecting sources for spare-parts planning.
The contractor shall publish a logistics schedule for spare parts before the next planning cycle.
Vendors must demonstrate a written maintenance procedure for the spare-parts room.
The objective is to reduce delays when a part is not on the shelf.`;

const quiet = `The office is exploring ideas for a future infrastructure study.
Interested readers may review the public description and wait for a later notice.
The objective is to improve situational awareness before any requirement is written.`;

export const DEMO_SAMPLES: DemoSample[] = [
  {
    id: "water",
    externalId: "SAMPLE-WATER",
    title: "Water-network sensor prototype (sample)",
    blurb: "Mandatory and optional sentences, a standards line, and all three match dispositions.",
    opportunityType: "RFP",
    deadline: "2026-12-18T17:00:00-05:00",
    text: water,
  },
  {
    id: "port",
    externalId: "SAMPLE-PORT",
    title: "Port spare-parts schedule (sample)",
    blurb: "A short sources-sought note with a logistics line and a maintenance line.",
    opportunityType: "SOURCES_SOUGHT",
    deadline: "2026-11-30T15:00:00-05:00",
    text: port,
  },
  {
    id: "quiet",
    externalId: "SAMPLE-QUIET",
    title: "Vague forecast note (sample)",
    blurb: "No explicit requirement keywords, so the parser keeps the plan and flags review.",
    opportunityType: "FORECAST",
    deadline: "2027-03-01T17:00:00-05:00",
    text: quiet,
  },
];

export function findSample(id: string | undefined): DemoSample | undefined {
  if (!id) return undefined;
  return DEMO_SAMPLES.find((sample) => sample.id === id);
}
