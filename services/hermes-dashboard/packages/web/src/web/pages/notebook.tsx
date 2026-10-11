import { useEffect, useRef, useState } from "react";
import { Shell } from "../components/shell";
import { ControlButton, Panel, StatusPill } from "../components/instruments";
import { Markdown } from "../lib/markdown";
import { client } from "../lib/api";
import {
  useCreateNotebook,
  useDeleteCell,
  useGalaxyMap,
  useMemory,
  useNotebook,
  useNotebooks,
  useSaveCell,
} from "../queries/galaxy";

type CellRow = {
  id: number;
  notebookId: number;
  position: number;
  kind: string;
  source: string;
  output: string;
};

function format(value: unknown): string {
  if (value === undefined) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

/**
 * In-page kernel. No remote runtime: the cell body becomes an async function
 * with shared memory, the galaxy, and a local-model call injected. Nothing
 * leaves the machine the browser runs on.
 */
async function runCell(
  source: string,
  scope: { memory: unknown[]; nodes: unknown[]; links: unknown[] },
): Promise<string> {
  const logs: string[] = [];
  const print = (...args: unknown[]) => logs.push(args.map(format).join(" "));
  const jarvis = async (prompt: string) => {
    const res = await client.jarvis.ask({ prompt, history: [] });
    return res.answer;
  };

  try {
    // eslint-disable-next-line no-new-func
    const fn = new Function(
      "memory",
      "nodes",
      "links",
      "print",
      "jarvis",
      `return (async () => {\n${source}\n})()`,
    ) as (
      memory: unknown[],
      nodes: unknown[],
      links: unknown[],
      print: (...a: unknown[]) => void,
      jarvis: (p: string) => Promise<string>,
    ) => Promise<unknown>;

    const value = await fn(scope.memory, scope.nodes, scope.links, print, jarvis);
    const tail = format(value);
    return [...logs, tail].filter(Boolean).join("\n");
  } catch (err) {
    return [...logs, `Error: ${err instanceof Error ? err.message : String(err)}`].join("\n");
  }
}

function Cell({
  cell,
  scope,
  onSave,
  onDelete,
}: {
  cell: CellRow;
  scope: { memory: unknown[]; nodes: unknown[]; links: unknown[] };
  onSave: (patch: { kind: string; source: string; output: string }) => void;
  onDelete: () => void;
}) {
  const [source, setSource] = useState(cell.source);
  const [kind, setKind] = useState(cell.kind);
  const [output, setOutput] = useState(cell.output);
  const [editing, setEditing] = useState(cell.kind === "js");
  const [busy, setBusy] = useState(false);
  const area = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setSource(cell.source);
    setOutput(cell.output);
    setKind(cell.kind);
  }, [cell.id, cell.source, cell.output, cell.kind]);

  const run = async () => {
    if (kind === "markdown") {
      onSave({ kind, source, output: "" });
      setEditing(false);
      return;
    }
    setBusy(true);
    const result = await runCell(source, scope);
    setOutput(result);
    setBusy(false);
    onSave({ kind, source, output: result });
  };

  return (
    <div className="panel">
      <header className="flex items-center gap-2 border-b border-border px-2.5 py-1.5">
        <button
          type="button"
          onClick={() => {
            const next = kind === "js" ? "markdown" : "js";
            setKind(next);
            onSave({ kind: next, source, output });
          }}
          className="font-mono text-[10px] uppercase tracking-[0.14em] text-steel-bright"
        >
          {kind === "js" ? "js" : "md"}
        </button>
        <span className="data-label">cell {cell.position + 1}</span>
        <div className="ml-auto flex items-center gap-2">
          {busy && <StatusPill tone="armed" label="running" pulse />}
          <ControlButton onClick={() => setEditing((v) => !v)}>
            {editing ? "Preview" : "Edit"}
          </ControlButton>
          <ControlButton tone="live" onClick={() => void run()}>
            {kind === "js" ? "Run" : "Render"}
          </ControlButton>
          <ControlButton tone="breach" onClick={onDelete}>
            Del
          </ControlButton>
        </div>
      </header>

      {editing ? (
        <textarea
          ref={area}
          value={source}
          spellCheck={false}
          onChange={(e) => setSource(e.target.value)}
          onBlur={() => onSave({ kind, source, output })}
          onKeyDown={(e) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
              e.preventDefault();
              void run();
            }
          }}
          aria-label={`Cell ${cell.position + 1} source`}
          rows={Math.max(3, source.split("\n").length + 1)}
          className="w-full resize-y bg-obsidian p-3 font-mono text-[12px] leading-relaxed text-platinum outline-none"
        />
      ) : (
        <div className="px-3 py-1">
          {kind === "markdown" ? (
            <Markdown source={source} />
          ) : (
            <pre className="scroll-thin overflow-x-auto py-2 font-mono text-[12px] text-platinum-dim">
              {source}
            </pre>
          )}
        </div>
      )}

      {output && (
        <div className="border-t border-border bg-obsidian/60 px-3 py-2">
          <p className="data-label mb-1">output</p>
          <pre className="scroll-thin max-h-72 overflow-auto font-mono text-[12px] leading-relaxed whitespace-pre-wrap text-live">
            {output}
          </pre>
        </div>
      )}
    </div>
  );
}

function NotebookPage() {
  const notebooks = useNotebooks();
  const [activeId, setActiveId] = useState<number | null>(null);
  const notebook = useNotebook(activeId);
  const memory = useMemory();
  const map = useGalaxyMap();

  const saveCell = useSaveCell();
  const deleteCell = useDeleteCell();
  const createNotebook = useCreateNotebook();
  const [newTitle, setNewTitle] = useState("");

  useEffect(() => {
    if (activeId === null && (notebooks.data?.length ?? 0) > 0) {
      setActiveId(notebooks.data![0].id);
    }
  }, [notebooks.data, activeId]);

  const cells = (notebook.data?.cells ?? []) as CellRow[];
  const scope = {
    memory: memory.data ?? [],
    nodes: map.data?.nodes ?? [],
    links: map.data?.links ?? [],
  };

  const addCell = (kind: "markdown" | "js") => {
    if (activeId === null) return;
    saveCell.mutate({
      notebookId: activeId,
      position: cells.length,
      kind,
      source: kind === "js" ? "return nodes.length;" : "## New section\n",
      output: "",
    });
  };

  return (
    <Shell>
      <div className="grid gap-4 p-4 lg:grid-cols-[260px_minmax(0,1fr)]">
        <div className="flex flex-col gap-4">
          <Panel title="Notebooks">
            <div className="divide-y divide-border">
              {(notebooks.data ?? []).map((nb) => (
                <button
                  key={nb.id}
                  type="button"
                  onClick={() => setActiveId(nb.id)}
                  className={`block w-full px-3 py-2.5 text-left ${
                    nb.id === activeId ? "bg-steel/12" : "hover:bg-steel/8"
                  }`}
                >
                  <p className="font-display text-[12px] font-semibold tracking-wide text-platinum">
                    {nb.title}
                  </p>
                  <p className="font-mono text-[10px] text-platinum-dim">#{nb.id}</p>
                </button>
              ))}
            </div>
            <div className="flex gap-2 border-t border-border p-2.5">
              <input
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                aria-label="New notebook title"
                placeholder="new notebook"
                className="min-w-0 flex-1 border border-border bg-obsidian px-2 py-1 font-mono text-[11px] text-platinum outline-none focus:border-steel-bright"
              />
              <ControlButton
                disabled={!newTitle.trim()}
                onClick={() =>
                  createNotebook.mutate(
                    { title: newTitle.trim() },
                    {
                      onSuccess: (nb) => {
                        setActiveId(nb.id);
                        setNewTitle("");
                      },
                    },
                  )
                }
              >
                Add
              </ControlButton>
            </div>
          </Panel>

          <Panel title="Kernel scope" delay={40}>
            <div className="p-3">
              <p className="text-[12px] leading-relaxed text-platinum-dim">
                JS cells run in-page — no kernel, no remote runtime. Injected:
              </p>
              <ul className="mt-2 space-y-1 font-mono text-[11px] text-platinum">
                <li>memory[{scope.memory.length}]</li>
                <li>nodes[{scope.nodes.length}]</li>
                <li>links[{scope.links.length}]</li>
                <li>print(...args)</li>
                <li>await jarvis(prompt)</li>
              </ul>
              <p className="mt-2 font-mono text-[10px] text-platinum-dim">
                ⌘/ctrl + enter runs a cell
              </p>
            </div>
          </Panel>
        </div>

        <div className="flex min-w-0 flex-col gap-3">
          <div className="flex items-center gap-2">
            <h1 className="font-display text-[18px] font-bold tracking-wide text-platinum uppercase">
              {notebook.data?.notebook.title ?? "…"}
            </h1>
            <div className="ml-auto flex gap-2">
              <ControlButton onClick={() => addCell("markdown")}>+ markdown</ControlButton>
              <ControlButton onClick={() => addCell("js")}>+ js</ControlButton>
            </div>
          </div>

          {cells.map((cell) => (
            <Cell
              key={cell.id}
              cell={cell}
              scope={scope}
              onSave={(patch) =>
                saveCell.mutate({
                  id: cell.id,
                  notebookId: cell.notebookId,
                  position: cell.position,
                  kind: patch.kind as "markdown" | "js",
                  source: patch.source,
                  output: patch.output,
                })
              }
              onDelete={() => deleteCell.mutate({ id: cell.id })}
            />
          ))}
          {cells.length === 0 && (
            <p className="font-mono text-[11px] text-platinum-dim">
              no cells — add one above
            </p>
          )}
        </div>
      </div>
    </Shell>
  );
}

export default NotebookPage;
