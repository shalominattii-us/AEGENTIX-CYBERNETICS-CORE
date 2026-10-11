import { z } from "zod";
import { desc } from "drizzle-orm";
import { authed } from "../middleware/auth";
import { db } from "../database";
import * as schema from "../database/schema";
import { seedGalaxyIfEmpty } from "../lib/galaxy-seed";

/**
 * JARVIS — the assistant layer of the sovereign OS.
 *
 * Inference is served by the operator's own machines: Ollama (:11434) and
 * LM Studio's OpenAI-compatible surface (:1234). Nothing is sent to a hosted
 * provider. When no local endpoint answers, Jarvis degrades to a deterministic
 * local responder that still reads shared memory and the galaxy — so the console
 * is never dead, just plainly marked OFFLINE.
 */

const DEFAULT_ENDPOINTS = [
  { label: "LM Studio", url: "http://localhost:1234/v1", kind: "openai" as const },
  { label: "Ollama", url: "http://localhost:11434/v1", kind: "openai" as const },
];

function endpointsFromEnv() {
  const extra = process.env.JARVIS_ENDPOINTS;
  if (!extra) return DEFAULT_ENDPOINTS;
  return extra.split(",").map((url) => ({
    label: new URL(url).host,
    url: url.replace(/\/$/, ""),
    kind: "openai" as const,
  }));
}

async function probe(url: string) {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1200);
    const res = await fetch(`${url}/models`, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) return { up: false as const, models: [] as string[] };
    const data = (await res.json()) as { data?: { id: string }[] };
    return { up: true as const, models: (data.data ?? []).map((m) => m.id) };
  } catch {
    return { up: false as const, models: [] as string[] };
  }
}

/** Builds the system prompt: sovereign posture plus live memory and galaxy index. */
async function buildContext() {
  await seedGalaxyIfEmpty();
  const [mem, nodes] = await Promise.all([
    db.select().from(schema.memory).orderBy(desc(schema.memory.at)).limit(40),
    db.select().from(schema.nodes),
  ]);

  const arms = new Map<string, string[]>();
  for (const n of nodes) {
    if (!arms.has(n.cluster)) arms.set(n.cluster, []);
    arms.get(n.cluster)!.push(n.title);
  }

  const memoryBlock = mem.map((m) => `- ${m.key}: ${m.value} (${m.author})`).join("\n");
  const galaxyBlock = [...arms.entries()]
    .map(([cluster, titles]) => `- ${cluster}: ${titles.slice(0, 18).join(", ")}`)
    .join("\n");

  return {
    mem,
    nodes,
    system: `You are JARVIS, the assistant layer of a sovereign, fully-local AI operating system. You run on the operator's own hardware. Be direct and technical; no filler.

SHARED MEMORY:
${memoryBlock}

GALAXY INDEX (${nodes.length} bodies):
${galaxyBlock}

Answer from this context when it is relevant. Say plainly when something is not in the corpus rather than inventing it.`,
  };
}

/** Deterministic fallback so the console works with no model loaded. */
function offlineAnswer(
  prompt: string,
  mem: (typeof schema.memory.$inferSelect)[],
  nodes: (typeof schema.nodes.$inferSelect)[],
) {
  const q = prompt.toLowerCase();
  const words = q.split(/\s+/).filter((w) => w.length > 3);

  const hitNodes = nodes
    .filter((n) => words.some((w) => n.title.toLowerCase().includes(w) || n.body.toLowerCase().includes(w)))
    .slice(0, 6);
  const hitMemory = mem
    .filter((m) => words.some((w) => m.key.toLowerCase().includes(w) || m.value.toLowerCase().includes(w)))
    .slice(0, 6);

  const parts = [
    "**JARVIS is offline** — no local model answered on :1234 or :11434, so this is a retrieval-only response from shared memory and the galaxy index.",
  ];
  if (hitMemory.length > 0) {
    parts.push(
      "\n**Shared memory**\n" + hitMemory.map((m) => `- \`${m.key}\` — ${m.value}`).join("\n"),
    );
  }
  if (hitNodes.length > 0) {
    parts.push(
      "\n**Galaxy bodies**\n" +
        hitNodes.map((n) => `- **${n.title}** (${n.cluster}) — ${n.body.slice(0, 160).replace(/\n/g, " ")}`).join("\n"),
    );
  }
  if (hitMemory.length === 0 && hitNodes.length === 0) {
    parts.push(
      `\nNothing in the corpus matched that. The galaxy holds ${nodes.length} bodies and ${mem.length} memory entries. Start Ollama or LM Studio on the unit for real reasoning.`,
    );
  }
  return parts.join("\n");
}

export const jarvis = {
  /** Which local inference endpoints are reachable and what they have loaded. */
  status: authed.handler(async () => {
    const endpoints = endpointsFromEnv();
    const probes = await Promise.all(
      endpoints.map(async (e) => ({ ...e, ...(await probe(e.url)) })),
    );
    const online = probes.find((p) => p.up);
    return {
      endpoints: probes,
      online: Boolean(online),
      activeModel: online?.models[0] ?? null,
    };
  }),

  ask: authed
    .input(
      z.object({
        prompt: z.string().min(1),
        history: z
          .array(z.object({ role: z.enum(["user", "assistant"]), content: z.string() }))
          .default([]),
      }),
    )
    .handler(async ({ input }) => {
      const ctx = await buildContext();
      const endpoints = endpointsFromEnv();

      for (const endpoint of endpoints) {
        const state = await probe(endpoint.url);
        if (!state.up) continue;
        try {
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), 120000);
          const res = await fetch(`${endpoint.url}/chat/completions`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            signal: controller.signal,
            body: JSON.stringify({
              model: state.models[0] ?? "local-model",
              messages: [
                { role: "system", content: ctx.system },
                ...input.history,
                { role: "user", content: input.prompt },
              ],
              temperature: 0.4,
              stream: false,
            }),
          });
          clearTimeout(timer);
          if (!res.ok) continue;
          const data = (await res.json()) as {
            choices?: { message?: { content?: string } }[];
          };
          const content = data.choices?.[0]?.message?.content;
          if (content) {
            return {
              answer: content,
              source: endpoint.label,
              model: state.models[0] ?? "local-model",
              online: true as const,
            };
          }
        } catch {
          continue;
        }
      }

      return {
        answer: offlineAnswer(input.prompt, ctx.mem, ctx.nodes),
        source: "local retrieval",
        model: null,
        online: false as const,
      };
    }),
};
