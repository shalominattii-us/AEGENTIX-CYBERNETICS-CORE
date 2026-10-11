import { useEffect, useRef, useState } from "react";
import { Shell } from "../components/shell";
import { ControlButton, Panel, StatusPill } from "../components/instruments";
import { Markdown } from "../lib/markdown";
import {
  useAskJarvis,
  useForgetMemory,
  useJarvisStatus,
  useMemory,
  useWriteMemory,
} from "../queries/galaxy";

type Turn = { role: "user" | "assistant"; content: string; meta?: string };

const PROMPTS = [
  "What is in the corpus about the Hermes Governor?",
  "Summarise the serving layer on the unit.",
  "Which arms of the galaxy hold the agent code?",
  "What is left before Antigravity can assimilate?",
];

function JarvisPage() {
  const status = useJarvisStatus();
  const memory = useMemory();
  const ask = useAskJarvis();
  const write = useWriteMemory();
  const forget = useForgetMemory();

  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [memKey, setMemKey] = useState("");
  const [memValue, setMemValue] = useState("");
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [turns, ask.isPending]);

  const send = (prompt: string) => {
    const text = prompt.trim();
    if (!text || ask.isPending) return;
    const history = turns.map((t) => ({ role: t.role, content: t.content }));
    setTurns((prev) => [...prev, { role: "user", content: text }]);
    setDraft("");
    ask.mutate(
      { prompt: text, history },
      {
        onSuccess: (res) => {
          setTurns((prev) => [
            ...prev,
            {
              role: "assistant",
              content: res.answer,
              meta: res.online ? `${res.source} · ${res.model ?? "local"}` : "local retrieval",
            },
          ]);
        },
        onError: (err) => {
          setTurns((prev) => [
            ...prev,
            { role: "assistant", content: `Transport error: ${err.message}`, meta: "error" },
          ]);
        },
      },
    );
  };

  return (
    <Shell flush>
      <div className="grid h-full grid-cols-1 lg:grid-cols-[minmax(0,1fr)_340px]">
        {/* ---------------- conversation ---------------- */}
        <div className="flex min-h-0 flex-col">
          <div className="flex flex-wrap items-center gap-2 border-b border-border px-4 py-2.5">
            <h1 className="font-display text-[16px] font-bold tracking-[0.1em] text-platinum uppercase">
              Jarvis
            </h1>
            <span className="font-mono text-[10px] text-platinum-dim">
              local inference only — nothing leaves the unit
            </span>
            <div className="ml-auto flex flex-wrap gap-2">
              {(status.data?.endpoints ?? []).map((e) => (
                <StatusPill
                  key={e.url}
                  tone={e.up ? "live" : "steel"}
                  label={`${e.label} ${e.up ? (e.models[0] ?? "loaded").slice(0, 20) : "down"}`}
                />
              ))}
            </div>
          </div>

          <div ref={scroller} className="scroll-thin min-h-0 flex-1 overflow-y-auto px-4 py-4">
            {turns.length === 0 && (
              <div className="max-w-2xl">
                <p className="text-[13px] leading-relaxed text-platinum-dim">
                  Jarvis reads shared memory and the galaxy index, then answers with whichever
                  local model is resident on{" "}
                  <span className="font-mono text-steel-bright">:1234</span> or{" "}
                  <span className="font-mono text-steel-bright">:11434</span>. With no model
                  loaded it degrades to retrieval over the same corpus and says so plainly.
                </p>
                <div className="mt-4 grid gap-2 sm:grid-cols-2">
                  {PROMPTS.map((p) => (
                    <button
                      key={p}
                      type="button"
                      onClick={() => send(p)}
                      className="border border-border px-3 py-2.5 text-left text-[12px] text-platinum-dim hover:border-steel-bright hover:text-platinum"
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="mx-auto flex max-w-3xl flex-col gap-4">
              {turns.map((turn, i) => (
                <div
                  key={i}
                  className={`animate-rise ${turn.role === "user" ? "self-end" : "self-start"} max-w-[92%]`}
                >
                  <p className="data-label mb-1">
                    {turn.role === "user" ? "operator" : `jarvis${turn.meta ? ` · ${turn.meta}` : ""}`}
                  </p>
                  {turn.role === "user" ? (
                    <p className="border border-steel/50 bg-steel/10 px-3 py-2 text-[13px] text-platinum">
                      {turn.content}
                    </p>
                  ) : (
                    <div className="panel px-3 py-1.5">
                      <Markdown source={turn.content} />
                    </div>
                  )}
                </div>
              ))}
              {ask.isPending && (
                <div className="self-start">
                  <StatusPill tone="armed" label="thinking" pulse />
                </div>
              )}
            </div>
          </div>

          <div className="flex items-end gap-2 border-t border-border p-3">
            <textarea
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(draft);
                }
              }}
              rows={2}
              aria-label="Message to Jarvis"
              placeholder="ask jarvis — enter to send, shift+enter for a newline"
              className="scroll-thin min-h-0 flex-1 resize-none border border-border bg-obsidian px-3 py-2 font-sans text-[13px] text-platinum outline-none focus:border-steel-bright placeholder:text-platinum-dim"
            />
            <ControlButton
              tone="live"
              disabled={!draft.trim() || ask.isPending}
              onClick={() => send(draft)}
              className="h-[42px]"
            >
              Send
            </ControlButton>
            <ControlButton onClick={() => setTurns([])} className="h-[42px]">
              Clear
            </ControlButton>
          </div>
        </div>

        {/* ---------------- shared memory ---------------- */}
        <div className="flex min-h-0 flex-col border-t border-border lg:border-t-0 lg:border-l">
          <Panel title="Shared memory" className="min-h-0 flex-1 border-0">
            <div className="flex flex-col gap-2 border-b border-border p-2.5">
              <input
                value={memKey}
                onChange={(e) => setMemKey(e.target.value)}
                aria-label="Memory key"
                placeholder="key e.g. serving/endpoints"
                className="border border-border bg-obsidian px-2 py-1.5 font-mono text-[11px] text-platinum outline-none focus:border-steel-bright"
              />
              <textarea
                value={memValue}
                onChange={(e) => setMemValue(e.target.value)}
                rows={2}
                aria-label="Memory value"
                placeholder="value — every agent reads this back"
                className="resize-none border border-border bg-obsidian px-2 py-1.5 font-mono text-[11px] text-platinum outline-none focus:border-steel-bright"
              />
              <ControlButton
                disabled={!memKey.trim() || !memValue.trim()}
                onClick={() =>
                  write.mutate(
                    {
                      key: memKey.trim(),
                      value: memValue.trim(),
                      author: "operator",
                      scope: "shared",
                    },
                    {
                      onSuccess: () => {
                        setMemKey("");
                        setMemValue("");
                      },
                    },
                  )
                }
              >
                Write memory
              </ControlButton>
            </div>

            <div className="scroll-thin min-h-0 flex-1 divide-y divide-border overflow-y-auto">
              {(memory.data ?? []).map((m) => (
                <div key={m.id} className="group px-2.5 py-2">
                  <div className="flex items-center gap-2">
                    <p className="font-mono text-[10px] text-steel-bright">{m.key}</p>
                    <button
                      type="button"
                      onClick={() => forget.mutate({ id: m.id })}
                      className="ml-auto font-mono text-[10px] text-platinum-dim opacity-0 transition-opacity group-hover:opacity-100 hover:text-breach"
                    >
                      forget
                    </button>
                  </div>
                  <p className="mt-0.5 text-[12px] leading-snug text-platinum-dim">{m.value}</p>
                  <p className="mt-0.5 font-mono text-[10px] text-steel">{m.author}</p>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </Shell>
  );
}

export default JarvisPage;
