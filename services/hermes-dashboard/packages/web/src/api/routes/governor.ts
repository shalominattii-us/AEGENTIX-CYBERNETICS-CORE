import { z } from "zod";
import { desc, eq, sql } from "drizzle-orm";
import { authed } from "../middleware/auth";
import { db } from "../database";
import * as schema from "../database/schema";
import { seedIfEmpty } from "../lib/seed";
import { probeGovernor } from "../lib/probe";

/** Reads the singleton governor state row, seeding the control plane on first touch. */
async function readState() {
  await seedIfEmpty();
  const [state] = await db.select().from(schema.governorState).limit(1);
  return state;
}

async function writeAudit(entry: {
  verdict: string;
  subject: string;
  reason: string;
  actor?: string;
}) {
  await db.insert(schema.auditLog).values({
    verdict: entry.verdict,
    subject: entry.subject,
    reason: entry.reason,
    actor: entry.actor ?? "operator",
  });
}

export const governor = {
  /** Full control-plane snapshot: posture, limits, positions, and live-link status. */
  snapshot: authed.handler(async () => {
    const state = await readState();
    const [limits, openPositions, link] = await Promise.all([
      db.select().from(schema.policyLimits).orderBy(schema.policyLimits.id),
      db.select().from(schema.positions).orderBy(schema.positions.id),
      probeGovernor(state.endpoint),
    ]);

    const exposureUsd = openPositions.reduce(
      (sum, p) => sum + p.quantity * p.markUsd,
      0,
    );
    const unrealizedUsd = openPositions.reduce(
      (sum, p) => sum + (p.quantity * p.markUsd - p.costUsd),
      0,
    );
    const breaches = limits.filter(
      (l) => l.enforced && l.consumed >= l.ceiling,
    ).length;

    return {
      state,
      limits,
      positions: openPositions,
      link,
      totals: { exposureUsd, unrealizedUsd, breaches },
    };
  }),

  /** Governor decision audit trail, newest first. */
  audit: authed
    .input(z.object({ limit: z.number().min(1).max(200).default(40) }))
    .handler(async ({ input }) => {
      await seedIfEmpty();
      return db
        .select()
        .from(schema.auditLog)
        .orderBy(desc(schema.auditLog.at))
        .limit(input.limit);
    }),

  /** Engage or release the kill switch. Engaging always forces mode back to halted. */
  setKillSwitch: authed
    .input(z.object({ engaged: z.boolean(), reason: z.string().min(1) }))
    .handler(async ({ input }) => {
      const state = await readState();
      await db
        .update(schema.governorState)
        .set({
          killSwitchEngaged: input.engaged,
          mode: input.engaged ? "halted" : "armed",
          updatedAt: new Date(),
        })
        .where(eq(schema.governorState.id, state.id));

      await writeAudit({
        verdict: input.engaged ? "halt" : "arm",
        subject: "kill_switch",
        reason: input.reason,
      });
      return { ok: true };
    }),

  /** Move between halted / armed / live. Live requires the proof gate to be cleared. */
  setMode: authed
    .input(
      z.object({
        mode: z.enum(["halted", "armed", "live"]),
        reason: z.string().min(1),
      }),
    )
    .handler(async ({ input }) => {
      const state = await readState();

      if (input.mode !== "halted" && state.killSwitchEngaged) {
        await writeAudit({
          verdict: "deny",
          subject: `mode:${input.mode}`,
          reason: "kill switch engaged — release before arming",
        });
        return { ok: false, denied: "KILL_SWITCH_ENGAGED" as const };
      }
      if (input.mode === "live" && state.paperProofGate) {
        await writeAudit({
          verdict: "deny",
          subject: "mode:live",
          reason: "paper-proof gate not cleared",
        });
        return { ok: false, denied: "PAPER_PROOF_GATE" as const };
      }

      await db
        .update(schema.governorState)
        .set({ mode: input.mode, updatedAt: new Date() })
        .where(eq(schema.governorState.id, state.id));
      await writeAudit({
        verdict: "allow",
        subject: `mode:${input.mode}`,
        reason: input.reason,
      });
      return { ok: true };
    }),

  /** Clear or re-arm the paper-proof gate that blocks live execution. */
  setProofGate: authed
    .input(z.object({ gated: z.boolean(), reason: z.string().min(1) }))
    .handler(async ({ input }) => {
      const state = await readState();
      await db
        .update(schema.governorState)
        .set({
          paperProofGate: input.gated,
          mode: input.gated && state.mode === "live" ? "armed" : state.mode,
          updatedAt: new Date(),
        })
        .where(eq(schema.governorState.id, state.id));
      await writeAudit({
        verdict: input.gated ? "halt" : "override",
        subject: "paper_proof_gate",
        reason: input.reason,
      });
      return { ok: true };
    }),

  /** Point the dashboard at a different Hermes Governor endpoint. */
  setEndpoint: authed
    .input(z.object({ endpoint: z.string().min(1) }))
    .handler(async ({ input }) => {
      const state = await readState();
      await db
        .update(schema.governorState)
        .set({ endpoint: input.endpoint, updatedAt: new Date() })
        .where(eq(schema.governorState.id, state.id));
      await writeAudit({
        verdict: "allow",
        subject: "endpoint",
        reason: `control endpoint set to ${input.endpoint}`,
      });
      return { ok: true, link: await probeGovernor(input.endpoint) };
    }),

  /** Toggle enforcement on a single policy limit. */
  setLimitEnforced: authed
    .input(z.object({ id: z.number(), enforced: z.boolean() }))
    .handler(async ({ input }) => {
      const [limit] = await db
        .select()
        .from(schema.policyLimits)
        .where(eq(schema.policyLimits.id, input.id));
      if (!limit) return { ok: false };
      await db
        .update(schema.policyLimits)
        .set({ enforced: input.enforced })
        .where(eq(schema.policyLimits.id, input.id));
      await writeAudit({
        verdict: input.enforced ? "allow" : "override",
        subject: `limit:${limit.name}`,
        reason: input.enforced
          ? "enforcement enabled"
          : "enforcement suspended by operator",
      });
      return { ok: true };
    }),

  /** Reset consumed counters for the current window. */
  resetWindow: authed.handler(async () => {
    await readState();
    await db
      .update(schema.policyLimits)
      .set({ consumed: sql`0` });
    await writeAudit({
      verdict: "allow",
      subject: "policy_window",
      reason: "consumption counters reset",
    });
    return { ok: true };
  }),
};
