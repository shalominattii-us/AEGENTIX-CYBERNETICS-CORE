import { z } from "zod";
import { desc, eq, or } from "drizzle-orm";
import { authed } from "../middleware/auth";
import { db } from "../database";
import * as schema from "../database/schema";
import { seedGalaxyIfEmpty } from "../lib/galaxy-seed";

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

/** Re-derives wikilink edges for one node after its body changes. */
async function syncWikilinks(nodeId: number, body: string) {
  await db
    .delete(schema.links)
    .where(eq(schema.links.sourceId, nodeId));

  const all = await db.select().from(schema.nodes);
  const bySlug = new Map(all.map((n) => [n.slug, n]));
  const edges: { sourceId: number; targetId: number; relation: string }[] = [];

  for (const match of body.matchAll(/\[\[([^\]]+)\]\]/g)) {
    const target = bySlug.get(slugify(match[1]));
    if (target && target.id !== nodeId) {
      edges.push({ sourceId: nodeId, targetId: target.id, relation: "wikilink" });
    }
  }
  if (edges.length > 0) await db.insert(schema.links).values(edges);
}

export const galaxy = {
  /** Every body and edge in the galaxy — the map the renderer draws. */
  map: authed.handler(async () => {
    await seedGalaxyIfEmpty();
    const [allNodes, allLinks] = await Promise.all([
      db.select().from(schema.nodes).orderBy(schema.nodes.id),
      db.select().from(schema.links),
    ]);
    const clusters = [...new Set(allNodes.map((n) => n.cluster))].sort();
    return { nodes: allNodes, links: allLinks, clusters };
  }),

  node: authed
    .input(z.object({ id: z.number() }))
    .handler(async ({ input }) => {
      const [node] = await db
        .select()
        .from(schema.nodes)
        .where(eq(schema.nodes.id, input.id));
      if (!node) return null;

      const edges = await db
        .select()
        .from(schema.links)
        .where(
          or(
            eq(schema.links.sourceId, node.id),
            eq(schema.links.targetId, node.id),
          ),
        );
      const noteMemory = await db
        .select()
        .from(schema.memory)
        .where(eq(schema.memory.nodeId, node.id));
      return { node, edges, memory: noteMemory };
    }),

  saveNode: authed
    .input(
      z.object({
        id: z.number().optional(),
        title: z.string().min(1),
        kind: z.enum(["star", "planet", "agent"]).default("planet"),
        cluster: z.string().default("unsorted"),
        body: z.string().default(""),
      }),
    )
    .handler(async ({ input }) => {
      await seedGalaxyIfEmpty();
      if (input.id) {
        await db
          .update(schema.nodes)
          .set({
            title: input.title,
            kind: input.kind,
            cluster: input.cluster,
            body: input.body,
            mass: Math.max(1, Math.log10(input.body.length + 10)),
            updatedAt: new Date(),
          })
          .where(eq(schema.nodes.id, input.id));
        await syncWikilinks(input.id, input.body);
        return { id: input.id };
      }

      const [created] = await db
        .insert(schema.nodes)
        .values({
          slug: slugify(input.title) || `node-${Date.now()}`,
          title: input.title,
          kind: input.kind,
          cluster: input.cluster,
          body: input.body,
          mass: Math.max(1, Math.log10(input.body.length + 10)),
        })
        .returning();
      await syncWikilinks(created.id, input.body);
      return { id: created.id };
    }),

  deleteNode: authed
    .input(z.object({ id: z.number() }))
    .handler(async ({ input }) => {
      await db.delete(schema.nodes).where(eq(schema.nodes.id, input.id));
      await db.delete(schema.links).where(eq(schema.links.sourceId, input.id));
      await db.delete(schema.links).where(eq(schema.links.targetId, input.id));
      return { ok: true };
    }),

  /* ---------------- shared memory ---------------- */

  memory: authed.handler(async () => {
    await seedGalaxyIfEmpty();
    return db.select().from(schema.memory).orderBy(desc(schema.memory.at));
  }),

  writeMemory: authed
    .input(
      z.object({
        key: z.string().min(1),
        value: z.string().min(1),
        author: z.string().default("operator"),
        scope: z.string().default("shared"),
        nodeId: z.number().optional(),
      }),
    )
    .handler(async ({ input }) => {
      const [row] = await db.insert(schema.memory).values(input).returning();
      return row;
    }),

  forgetMemory: authed
    .input(z.object({ id: z.number() }))
    .handler(async ({ input }) => {
      await db.delete(schema.memory).where(eq(schema.memory.id, input.id));
      return { ok: true };
    }),

  /* ---------------- notebooks ---------------- */

  notebooks: authed.handler(async () => {
    await seedGalaxyIfEmpty();
    return db.select().from(schema.notebooks).orderBy(schema.notebooks.id);
  }),

  notebook: authed
    .input(z.object({ id: z.number() }))
    .handler(async ({ input }) => {
      const [nb] = await db
        .select()
        .from(schema.notebooks)
        .where(eq(schema.notebooks.id, input.id));
      if (!nb) return null;
      const nbCells = await db
        .select()
        .from(schema.cells)
        .where(eq(schema.cells.notebookId, nb.id))
        .orderBy(schema.cells.position);
      return { notebook: nb, cells: nbCells };
    }),

  createNotebook: authed
    .input(z.object({ title: z.string().min(1) }))
    .handler(async ({ input }) => {
      const [nb] = await db.insert(schema.notebooks).values(input).returning();
      await db.insert(schema.cells).values({
        notebookId: nb.id,
        position: 0,
        kind: "markdown",
        source: `# ${input.title}\n`,
      });
      return nb;
    }),

  saveCell: authed
    .input(
      z.object({
        id: z.number().optional(),
        notebookId: z.number(),
        position: z.number().default(0),
        kind: z.enum(["markdown", "js"]).default("markdown"),
        source: z.string().default(""),
        output: z.string().default(""),
      }),
    )
    .handler(async ({ input }) => {
      if (input.id) {
        await db
          .update(schema.cells)
          .set({
            kind: input.kind,
            source: input.source,
            output: input.output,
            position: input.position,
          })
          .where(eq(schema.cells.id, input.id));
        return { id: input.id };
      }
      const [cell] = await db.insert(schema.cells).values(input).returning();
      return { id: cell.id };
    }),

  deleteCell: authed
    .input(z.object({ id: z.number() }))
    .handler(async ({ input }) => {
      await db.delete(schema.cells).where(eq(schema.cells.id, input.id));
      return { ok: true };
    }),
};
