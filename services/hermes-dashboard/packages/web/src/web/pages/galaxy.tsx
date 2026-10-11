import { useMemo, useState } from "react";
import { Shell } from "../components/shell";
import { GalaxyCanvas } from "../components/galaxy-canvas";
import { ControlButton, Panel, StatusPill, type Tone } from "../components/instruments";
import { Markdown } from "../lib/markdown";
import {
  useDeleteNode,
  useGalaxyMap,
  useNode,
  useSaveNode,
} from "../queries/galaxy";

const KINDS = ["star", "planet", "agent"] as const;

function kindTone(kind: string): Tone {
  return kind === "star" ? "steel" : kind === "agent" ? "live" : "armed";
}

function GalaxyPage() {
  const map = useGalaxyMap();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [cluster, setCluster] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({
    title: "",
    kind: "planet" as (typeof KINDS)[number],
    cluster: "unsorted",
    body: "",
  });

  const detail = useNode(selectedId);
  const saveNode = useSaveNode();
  const deleteNode = useDeleteNode();

  const nodes = useMemo(() => map.data?.nodes ?? [], [map.data]);
  const links = useMemo(() => map.data?.links ?? [], [map.data]);
  const clusters = map.data?.clusters ?? [];

  const byId = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);
  const bySlug = useMemo(() => new Map(nodes.map((n) => [n.slug, n])), [nodes]);

  const node = detail.data?.node ?? null;
  const edges = detail.data?.edges ?? [];

  const openWikilink = (label: string) => {
    const slug = label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
    const target = bySlug.get(slug);
    if (target) {
      setSelectedId(target.id);
      setEditing(false);
    }
  };

  const startEdit = () => {
    if (!node) return;
    setDraft({
      title: node.title,
      kind: (KINDS.includes(node.kind as (typeof KINDS)[number])
        ? node.kind
        : "planet") as (typeof KINDS)[number],
      cluster: node.cluster,
      body: node.body,
    });
    setEditing(true);
  };

  const startNew = () => {
    setSelectedId(null);
    setDraft({ title: "", kind: "planet", cluster: cluster ?? "unsorted", body: "" });
    setEditing(true);
  };

  const commit = () => {
    saveNode.mutate(
      {
        id: selectedId ?? undefined,
        title: draft.title.trim() || "untitled body",
        kind: draft.kind,
        cluster: draft.cluster.trim() || "unsorted",
        body: draft.body,
      },
      {
        onSuccess: (res) => {
          setSelectedId(res.id);
          setEditing(false);
        },
      },
    );
  };

  return (
    <Shell flush>
      <div className="grid h-full grid-cols-1 lg:grid-cols-[minmax(0,1fr)_400px]">
        {/* ---------------- map ---------------- */}
        <div className="relative min-h-[360px]">
          <GalaxyCanvas
            nodes={nodes}
            links={links}
            selectedId={selectedId}
            onSelect={(id) => {
              setSelectedId(id);
              setEditing(false);
            }}
            filterCluster={cluster}
            query={query}
          />

          <div className="pointer-events-none absolute inset-x-0 top-0 flex flex-wrap items-start gap-2 p-3">
            <div className="pointer-events-auto flex items-center gap-2 border border-border bg-obsidian/85 px-2 py-1.5 backdrop-blur">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                aria-label="Search galaxy bodies"
                placeholder="search bodies"
                spellCheck={false}
                className="w-40 bg-transparent font-mono text-[11px] text-platinum outline-none placeholder:text-platinum-dim"
              />
              <span className="font-mono text-[10px] text-steel">{nodes.length}</span>
            </div>
            <div className="pointer-events-auto flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setCluster(null)}
                className={`border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.12em] ${
                  cluster === null
                    ? "border-steel-bright/70 bg-steel/15 text-platinum"
                    : "border-border bg-obsidian/80 text-platinum-dim hover:text-platinum"
                }`}
              >
                all arms
              </button>
              {clusters.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => setCluster(cluster === c ? null : c)}
                  className={`border px-2 py-1 font-mono text-[10px] uppercase tracking-[0.12em] ${
                    cluster === c
                      ? "border-steel-bright/70 bg-steel/15 text-platinum"
                      : "border-border bg-obsidian/80 text-platinum-dim hover:text-platinum"
                  }`}
                >
                  {c}
                </button>
              ))}
            </div>
            <div className="pointer-events-auto ml-auto">
              <ControlButton
                onClick={startNew}
                className="border-border bg-obsidian/85 backdrop-blur"
              >
                + note
              </ControlButton>
            </div>
          </div>

          <p className="pointer-events-none absolute bottom-3 left-3 font-mono text-[10px] text-platinum-dim">
            drag to pan · wheel to zoom · click a body
          </p>
        </div>

        {/* ---------------- inspector ---------------- */}
        <div className="flex min-h-0 flex-col border-t border-border lg:border-t-0 lg:border-l">
          {editing ? (
            <Panel
              title={selectedId ? "Edit body" : "New body"}
              className="min-h-0 flex-1 border-0"
              right={
                <div className="flex gap-2">
                  <ControlButton tone="live" onClick={commit}>
                    Save
                  </ControlButton>
                  <ControlButton onClick={() => setEditing(false)}>Cancel</ControlButton>
                </div>
              }
            >
              <div className="flex min-h-0 flex-1 flex-col gap-2 p-3">
                <input
                  value={draft.title}
                  onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                  aria-label="Body title"
                  placeholder="title"
                  className="border border-border bg-obsidian px-2.5 py-1.5 font-display text-[14px] text-platinum outline-none focus:border-steel-bright"
                />
                <div className="flex gap-2">
                  <select
                    aria-label="Body kind"
                    value={draft.kind}
                    onChange={(e) =>
                      setDraft({ ...draft, kind: e.target.value as (typeof KINDS)[number] })
                    }
                    className="border border-border bg-obsidian px-2 py-1.5 font-mono text-[11px] text-platinum outline-none"
                  >
                    {KINDS.map((k) => (
                      <option key={k} value={k}>
                        {k}
                      </option>
                    ))}
                  </select>
                  <input
                    value={draft.cluster}
                    onChange={(e) => setDraft({ ...draft, cluster: e.target.value })}
                    aria-label="Cluster"
                    placeholder="cluster"
                    className="flex-1 border border-border bg-obsidian px-2.5 py-1.5 font-mono text-[11px] text-platinum outline-none focus:border-steel-bright"
                  />
                </div>
                <textarea
                  value={draft.body}
                  onChange={(e) => setDraft({ ...draft, body: e.target.value })}
                  aria-label="Body markdown"
                  placeholder="markdown body — [[wikilinks]] become edges in the galaxy"
                  spellCheck={false}
                  className="scroll-thin min-h-0 flex-1 resize-none border border-border bg-obsidian p-2.5 font-mono text-[12px] leading-relaxed text-platinum outline-none focus:border-steel-bright"
                />
              </div>
            </Panel>
          ) : node ? (
            <Panel
              title={node.cluster}
              className="min-h-0 flex-1 border-0"
              right={
                <div className="flex gap-2">
                  <ControlButton onClick={startEdit}>Edit</ControlButton>
                  <ControlButton
                    tone="breach"
                    onClick={() => {
                      deleteNode.mutate({ id: node.id });
                      setSelectedId(null);
                    }}
                  >
                    Delete
                  </ControlButton>
                </div>
              }
            >
              <div className="scroll-thin min-h-0 flex-1 overflow-y-auto">
                <div className="border-b border-border px-3 py-3">
                  <div className="flex items-center gap-2">
                    <StatusPill tone={kindTone(node.kind)} label={node.kind} />
                    <span className="font-mono text-[10px] text-platinum-dim">{node.slug}</span>
                  </div>
                  <h1 className="mt-2 font-display text-[20px] font-bold tracking-wide text-platinum">
                    {node.title}
                  </h1>
                  {node.meta && (
                    <p className="mt-1.5 font-mono text-[10px] text-steel">
                      {Object.entries(node.meta)
                        .map(([k, v]) => `${k}=${String(v)}`)
                        .join(" · ")}
                    </p>
                  )}
                </div>

                <div className="px-3 py-2">
                  <Markdown source={node.body} onWikilink={openWikilink} />
                </div>

                <div className="border-t border-border px-3 py-3">
                  <p className="panel-title mb-2">Edges · {edges.length}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {edges.map((edge) => {
                      const otherId =
                        edge.sourceId === node.id ? edge.targetId : edge.sourceId;
                      const other = byId.get(otherId);
                      if (!other) return null;
                      return (
                        <button
                          key={edge.id}
                          type="button"
                          onClick={() => setSelectedId(other.id)}
                          className="border border-border px-2 py-1 font-mono text-[10px] text-platinum-dim hover:border-steel-bright hover:text-platinum"
                        >
                          {edge.sourceId === node.id ? "→ " : "← "}
                          {other.title}
                        </button>
                      );
                    })}
                    {edges.length === 0 && (
                      <p className="font-mono text-[10px] text-platinum-dim">
                        no edges — add [[wikilinks]] to bind this body
                      </p>
                    )}
                  </div>
                </div>

                {(detail.data?.memory ?? []).length > 0 && (
                  <div className="border-t border-border px-3 py-3">
                    <p className="panel-title mb-2">Attached memory</p>
                    {(detail.data?.memory ?? []).map((m) => (
                      <div key={m.id} className="mb-2">
                        <p className="font-mono text-[10px] text-steel-bright">{m.key}</p>
                        <p className="text-[12px] text-platinum-dim">{m.value}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Panel>
          ) : (
            <Panel title="Inspector" className="min-h-0 flex-1 border-0">
              <div className="p-3">
                <p className="text-[13px] leading-relaxed text-platinum-dim">
                  {nodes.length} bodies across {clusters.length} arms — one star per ingested
                  repository, plus the anchor notes that bind them. Click a body to read it, or
                  create a note and link it with <span className="font-mono">[[wikilinks]]</span>.
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  {clusters.map((c) => (
                    <div key={c} className="border border-border px-2.5 py-2">
                      <p className="data-label">{c}</p>
                      <p className="mt-1 font-mono text-[16px] text-platinum">
                        {nodes.filter((n) => n.cluster === c).length}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </Panel>
          )}
        </div>
      </div>
    </Shell>
  );
}

export default GalaxyPage;
