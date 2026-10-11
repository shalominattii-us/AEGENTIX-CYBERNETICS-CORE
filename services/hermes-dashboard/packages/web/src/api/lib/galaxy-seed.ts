import { db } from "../database";
import * as schema from "../database/schema";
import manifest from "./repo-manifest.json";

type RepoMeta = {
  name: string;
  private: boolean;
  fork: boolean;
  desc_field: string;
  size_kb: number;
  readme_snip: string;
};

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/** Groups a repo into a galaxy arm from its name. */
function clusterFor(name: string) {
  const n = name.toLowerCase();
  if (n.includes("sovereignos") || n.includes("sovereign-os")) return "SovereignOS";
  if (n.startsWith("sovereign") || n === "sovereign") return "Sovereign Core";
  if (n.includes("aegentix") || n.includes("aegentis")) return "AEGENTIX";
  if (n.includes("cyber") || n.includes("gym")) return "CyberGym";
  if (n.includes("brain") || n.includes("mem")) return "Cognition";
  if (n.includes("agent") || n.includes("swarm") || n.includes("mesh")) return "Agent Mesh";
  return "Outer Rim";
}

/**
 * Seeds the galaxy from the ingested GitHub corpus (83 repos) plus the
 * founding memory notes, then derives wikilink edges. Idempotent.
 */
let seeding: Promise<void> | undefined;

export function seedGalaxyIfEmpty() {
  seeding ??= seedGalaxy().catch((error) => {
    seeding = undefined;
    throw error;
  });
  return seeding;
}

async function seedGalaxy() {
  const existing = await db.select().from(schema.nodes).limit(1);
  if (existing.length > 0) return;

  const repos = manifest as RepoMeta[];

  const starRows = repos.map((r) => {
    const short = r.name.split("/")[1] ?? r.name;
    return {
      slug: `repo-${slugify(short)}`,
      title: short,
      kind: "star" as const,
      cluster: clusterFor(short),
      body:
        (r.desc_field || "No description recorded in the source repository.") +
        (r.readme_snip ? `\n\n${r.readme_snip}` : ""),
      // log scale so 175 GB repos don't dwarf the 0 KB ones off-screen
      mass: Math.max(1, Math.log10(r.size_kb + 10)),
      meta: {
        origin: r.name,
        private: r.private,
        fork: r.fork,
        sizeKb: r.size_kb,
      } as Record<string, unknown>,
    };
  });

  const noteRows = [
    {
      slug: "sovereign-os",
      title: "Sovereign OS",
      kind: "planet" as const,
      cluster: "Sovereign Core",
      mass: 3,
      body: `The unit runs fully local, unattended, production-deployable. No dependency on hosted inference.

Serving layer: [[ollama-armada]] on port 11434 alongside LM Studio on 1234 exposing an OpenAI-compatible surface.
Knowledge substrate: this galaxy — every ingested repo is a star, every memory note a planet.
Control plane for treasury actions: [[hermes-governor]].
Training and qualification: [[repo-cybergym]].`,
      meta: null,
    },
    {
      slug: "ollama-armada",
      title: "Ollama Armada",
      kind: "agent" as const,
      cluster: "Cognition",
      mass: 2.4,
      body: `Local model fleet on :11434. LM Studio runs beside it on :1234 with a Heretic-processed model loaded; the CyberGym lmstudio athlete adapter auto-detects whichever model is resident.

Feeds [[sovereign-os]] and every agent in [[agent-mesh]].`,
      meta: null,
    },
    {
      slug: "hermes-governor",
      title: "Hermes Governor",
      kind: "agent" as const,
      cluster: "AEGENTIX",
      mass: 2.6,
      body: `Treasury control API (spec port 9950; current deployment answers on 9119). Enforces spending limits, rate limits, and writes an audit trail for every decision.

Gatekeeper in front of the Coinbase CDP trading plugin — paper-proof gated with a kill switch. Live console is at /governor.

Governed by [[sovereign-os]].`,
      meta: null,
    },
    {
      slug: "agent-mesh",
      title: "Agent Mesh",
      kind: "agent" as const,
      cluster: "Agent Mesh",
      mass: 2.5,
      body: `Shared agentic layer: agents read and write one memory surface instead of holding private context. Every write lands in shared memory keyed by author, so an agent picking up a long-horizon task inherits what the last one learned.

Backed by [[ollama-armada]], indexed into this galaxy.`,
      meta: null,
    },
    {
      slug: "antigravity-assimilation",
      title: "Antigravity Assimilation",
      kind: "planet" as const,
      cluster: "Cognition",
      mass: 2.2,
      body: `End state: a sovereign frontier-level model doing unattended long-horizon work on the unit, assimilating the whole corpus.

Prerequisite is that everything is fully installed and operational locally — the galaxy is the index it reads, [[sovereign-os]] is the substrate it runs on.`,
      meta: null,
    },
  ];

  await db.insert(schema.nodes).values([...starRows, ...noteRows]).onConflictDoNothing();

  const all = await db.select().from(schema.nodes);
  const bySlug = new Map(all.map((n) => [n.slug, n]));

  const edges: { sourceId: number; targetId: number; relation: string }[] = [];

  // Wikilink edges from note bodies.
  for (const node of all) {
    for (const match of node.body.matchAll(/\[\[([^\]]+)\]\]/g)) {
      const target = bySlug.get(slugify(match[1]));
      if (target && target.id !== node.id) {
        edges.push({ sourceId: node.id, targetId: target.id, relation: "wikilink" });
      }
    }
  }

  // Cluster edges: every star binds to its cluster's anchor note so arms hold together.
  const anchorByCluster = new Map<string, number>([
    ["Sovereign Core", bySlug.get("sovereign-os")!.id],
    ["SovereignOS", bySlug.get("sovereign-os")!.id],
    ["AEGENTIX", bySlug.get("hermes-governor")!.id],
    ["Agent Mesh", bySlug.get("agent-mesh")!.id],
    ["Cognition", bySlug.get("ollama-armada")!.id],
    ["CyberGym", bySlug.get("agent-mesh")!.id],
    ["Outer Rim", bySlug.get("sovereign-os")!.id],
  ]);
  for (const node of all) {
    if (node.kind !== "star") continue;
    const anchor = anchorByCluster.get(node.cluster);
    if (anchor && anchor !== node.id) {
      edges.push({ sourceId: anchor, targetId: node.id, relation: "cluster" });
    }
  }

  if (edges.length > 0) await db.insert(schema.links).values(edges);

  await db.insert(schema.memory).values([
    {
      key: "ingest/github",
      value:
        "All 83 shalominattii-us repos consolidated into AEGENTIX-CYBERNETICS-CORE/sources (keep-all, no filtering). Snapshot 2026-09-20.",
      author: "runable",
      scope: "shared",
    },
    {
      key: "serving/endpoints",
      value: "Ollama :11434 · LM Studio :1234 (OpenAI-compatible, Heretic-processed model).",
      author: "operator",
      scope: "shared",
    },
    {
      key: "governor/endpoint",
      value: "Hermes Governor expected at localhost:9119 on the unit (spec default 9950).",
      author: "operator",
      scope: "shared",
    },
    {
      key: "constraints/sovereignty",
      value: "Free, local, unattended, production-deployable. No hosted inference dependency.",
      author: "operator",
      scope: "shared",
    },
  ]);

  const [nb] = await db
    .insert(schema.notebooks)
    .values({ title: "Sovereign Bootstrap" })
    .returning();

  await db.insert(schema.cells).values([
    {
      notebookId: nb.id,
      position: 0,
      kind: "markdown",
      source:
        "# Sovereign Bootstrap\n\nThis notebook runs **locally in the browser** — no kernel, no remote runtime. JS cells execute in-page; `memory` is injected so cells can read shared memory.",
    },
    {
      notebookId: nb.id,
      position: 1,
      kind: "js",
      source:
        "// Shared memory is injected into every JS cell.\nreturn memory.map(m => `${m.key} = ${m.value}`).join('\\n');",
    },
    {
      notebookId: nb.id,
      position: 2,
      kind: "js",
      source:
        "// Galaxy nodes are injected too — count the arms.\nconst arms = {};\nfor (const n of nodes) arms[n.cluster] = (arms[n.cluster] ?? 0) + 1;\nreturn arms;",
    },
  ]);
}
