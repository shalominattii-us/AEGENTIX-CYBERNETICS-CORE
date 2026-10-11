import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";

/**
 * Hermes Governor control-plane state.
 * Mirrors the AEGENTIX_TREASURY_LABS_SPECIFICATION Hermes Governor contract
 * (policy enforcement, spending limits, rate limiting, audit trail).
 */

/** Single-row table holding the live governor posture. */
export const governorState = sqliteTable("governor_state", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  /** halted | armed | live */
  mode: text("mode").notNull().default("halted"),
  killSwitchEngaged: integer("kill_switch_engaged", { mode: "boolean" })
    .notNull()
    .default(true),
  /** Trades execute against paper ledger until proof gate is cleared. */
  paperProofGate: integer("paper_proof_gate", { mode: "boolean" })
    .notNull()
    .default(true),
  endpoint: text("endpoint").notNull().default("http://localhost:9119"),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});

/** Spending / rate limits the governor enforces per window. */
export const policyLimits = sqliteTable("policy_limits", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  name: text("name").notNull(),
  /** e.g. USD, tx, req */
  unit: text("unit").notNull(),
  window: text("window").notNull(),
  ceiling: real("ceiling").notNull(),
  consumed: real("consumed").notNull().default(0),
  enforced: integer("enforced", { mode: "boolean" }).notNull().default(true),
});

/** Open positions / balances reported by the trading plugin. */
export const positions = sqliteTable("positions", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  asset: text("asset").notNull(),
  venue: text("venue").notNull(),
  quantity: real("quantity").notNull(),
  markUsd: real("mark_usd").notNull(),
  costUsd: real("cost_usd").notNull(),
  /** paper | live */
  ledger: text("ledger").notNull().default("paper"),
});

/* ------------------------------------------------------------------ *
 * SOVEREIGN OS — galaxy knowledge graph, shared memory, notebooks
 * ------------------------------------------------------------------ */

/** A body in the galaxy: a repo/system (star), a memory note (planet), an agent (probe). */
export const nodes = sqliteTable("nodes", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  slug: text("slug").notNull().unique(),
  title: text("title").notNull(),
  /** star | planet | agent */
  kind: text("kind").notNull().default("planet"),
  /** cluster/constellation name used for galaxy arm grouping */
  cluster: text("cluster").notNull().default("unsorted"),
  /** markdown body, supports [[wikilinks]] */
  body: text("body").notNull().default(""),
  /** relative visual weight (repo size, note length) */
  mass: real("mass").notNull().default(1),
  meta: text("meta", { mode: "json" }).$type<Record<string, unknown>>(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});

/** Directed edge between two nodes — derived from wikilinks or set explicitly. */
export const links = sqliteTable("links", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  sourceId: integer("source_id").notNull(),
  targetId: integer("target_id").notNull(),
  /** wikilink | cluster | manual */
  relation: text("relation").notNull().default("wikilink"),
});

/** Shared agent memory — the write surface every agent reads back from. */
export const memory = sqliteTable("memory", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  key: text("key").notNull(),
  value: text("value").notNull(),
  /** which agent/process wrote it */
  author: text("author").notNull().default("operator"),
  scope: text("scope").notNull().default("shared"),
  nodeId: integer("node_id"),
  at: integer("at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});

/** Notebook surface (Jupyter-style, executed locally in the browser). */
export const notebooks = sqliteTable("notebooks", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  title: text("title").notNull(),
  createdAt: integer("created_at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
});

export const cells = sqliteTable("cells", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  notebookId: integer("notebook_id").notNull(),
  position: integer("position").notNull().default(0),
  /** markdown | js */
  kind: text("kind").notNull().default("markdown"),
  source: text("source").notNull().default(""),
  output: text("output").notNull().default(""),
});

/** Immutable audit trail of governor decisions. */
export const auditLog = sqliteTable("audit_log", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  at: integer("at", { mode: "timestamp" })
    .notNull()
    .$defaultFn(() => new Date()),
  /** allow | deny | halt | arm | override */
  verdict: text("verdict").notNull(),
  subject: text("subject").notNull(),
  reason: text("reason").notNull(),
  actor: text("actor").notNull().default("operator"),
});
export * from "./auth-schema";
