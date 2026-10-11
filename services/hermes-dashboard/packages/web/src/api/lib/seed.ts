import { db } from "../database";
import * as schema from "../database/schema";

/**
 * Seeds the local control plane so the dashboard has coherent state before it is
 * pointed at a live Hermes Governor. Values mirror the treasury spec defaults:
 * halted, kill switch engaged, paper-proof gate closed.
 */
export async function seedIfEmpty() {
  const existing = await db.select().from(schema.governorState).limit(1);
  if (existing.length > 0) return;

  await db.insert(schema.governorState).values({
    mode: "halted",
    killSwitchEngaged: true,
    paperProofGate: true,
    endpoint: process.env.HERMES_GOVERNOR_URL ?? "http://localhost:9119",
  });

  await db.insert(schema.policyLimits).values([
    { name: "Daily notional", unit: "USD", window: "24h", ceiling: 25000, consumed: 4820, enforced: true },
    { name: "Per-trade ceiling", unit: "USD", window: "per tx", ceiling: 2500, consumed: 1180, enforced: true },
    { name: "Gas budget", unit: "USD", window: "24h", ceiling: 400, consumed: 96.4, enforced: true },
    { name: "Request rate", unit: "req", window: "1m", ceiling: 120, consumed: 37, enforced: true },
    { name: "Open position count", unit: "pos", window: "concurrent", ceiling: 8, consumed: 4, enforced: true },
  ]);

  await db.insert(schema.positions).values([
    { asset: "ETH", venue: "Coinbase CDP", quantity: 1.42, markUsd: 3180.44, costUsd: 4320.1, ledger: "paper" },
    { asset: "BTC", venue: "Coinbase CDP", quantity: 0.061, markUsd: 68420.0, costUsd: 4010.55, ledger: "paper" },
    { asset: "SOL", venue: "Coinbase CDP", quantity: 18.5, markUsd: 146.2, costUsd: 2890.0, ledger: "paper" },
    { asset: "USDC", venue: "Treasury float", quantity: 12400, markUsd: 1.0, costUsd: 12400.0, ledger: "paper" },
  ]);

  await db.insert(schema.auditLog).values([
    { verdict: "halt", subject: "kill_switch", reason: "cold start — governor initialised halted", actor: "system" },
    { verdict: "deny", subject: "mode:live", reason: "paper-proof gate not cleared", actor: "system" },
    { verdict: "allow", subject: "policy_window", reason: "limit set loaded from treasury spec", actor: "system" },
    { verdict: "deny", subject: "trade:SOL", reason: "per-trade ceiling would be exceeded (2,740 > 2,500)", actor: "hermes" },
    { verdict: "allow", subject: "trade:ETH", reason: "within daily notional and per-trade ceiling", actor: "hermes" },
  ]);
}
