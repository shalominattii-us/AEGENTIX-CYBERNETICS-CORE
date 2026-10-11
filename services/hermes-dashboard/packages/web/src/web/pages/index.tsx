import { useState } from "react";
import { Link } from "wouter";
import { Shell } from "../components/shell";
import { ControlButton, Metric, Panel, StatusPill, modeTone } from "../components/instruments";
import { useGalaxyMap, useJarvisStatus, useMemory, useNotebooks } from "../queries/galaxy";
import { useSnapshot } from "../queries/governor";

const SURFACES = [
  {
    href: "/governor",
    label: "Governor",
    line: "Treasury control plane — mode, kill switch, policy limits, audit trail.",
  },
  {
    href: "/galaxy",
    label: "Galaxy",
    line: "The whole ingested corpus as a map: one star per repo, wikilinked notes as planets.",
  },
  {
    href: "/notebook",
    label: "Notebook",
    line: "In-page kernel. JS cells over shared memory and the galaxy, no remote runtime.",
  },
  {
    href: "/jarvis",
    label: "Jarvis",
    line: "Local assistant on :1234 / :11434, grounded in shared memory. Degrades to retrieval.",
  },
];

const INSTALL = `# 1. Bring up the stack (PowerShell, elevated, from the repo root)
powershell -ExecutionPolicy Bypass -File .\\install\\bootstrap-unit.ps1

# Verifies Ollama :11434 and LM Studio :1234, pulls the fallback
# model, writes .env, pushes the schema, starts the console.

# 2. Make the unit operable from anywhere (no RDP on Win 11 Home)
powershell -ExecutionPolicy Bypass -File .\\install\\remote-access.ps1 -ExposeConsole

# Tailscale unattended mesh + RustDesk as a service with a
# permanent password. Survives reboot and logout.`;

function Deck() {
  const snapshot = useSnapshot();
  const map = useGalaxyMap();
  const memory = useMemory();
  const notebooks = useNotebooks();
  const jarvis = useJarvisStatus();
  const [copied, setCopied] = useState(false);

  const state = snapshot.data?.state;
  const nodes = map.data?.nodes ?? [];
  const stars = nodes.filter((n) => n.kind === "star").length;

  return (
    <Shell>
      <div className="mx-auto max-w-[1400px] p-4">
        <div className="animate-rise">
          <p className="data-label">Sovereign stack · operator deck</p>
          <h1 className="mt-1 font-display text-[30px] leading-none font-bold tracking-[0.06em] text-platinum uppercase">
            Hermes
          </h1>
          <p className="mt-2 max-w-2xl text-[13px] leading-relaxed text-platinum-dim">
            One console over the local stack: the Hermes Governor control plane, the ingested
            corpus as a navigable galaxy, a notebook that executes in-page, and Jarvis running on
            the unit&apos;s own models. Nothing here calls a hosted provider.
          </p>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Panel delay={40}>
            <Metric label="Corpus stars" value={String(stars)} sub="ingested repositories" />
          </Panel>
          <Panel delay={60}>
            <Metric
              label="Galaxy edges"
              value={String(map.data?.links.length ?? 0)}
              sub={`${map.data?.clusters.length ?? 0} arms`}
            />
          </Panel>
          <Panel delay={80}>
            <Metric
              label="Shared memory"
              value={String(memory.data?.length ?? 0)}
              sub={`${notebooks.data?.length ?? 0} notebooks`}
            />
          </Panel>
          <Panel delay={100}>
            <Metric
              label="Governor"
              value={(state?.mode ?? "…").toUpperCase()}
              tone={state ? modeTone(state.mode) : "steel"}
              sub={state?.endpoint}
            />
          </Panel>
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
          <div className="grid gap-4 sm:grid-cols-2">
            {SURFACES.map((s, i) => (
              <Link key={s.href} href={s.href}>
                <Panel
                  delay={120 + i * 20}
                  className="h-full cursor-pointer transition-colors hover:border-steel-bright/70"
                >
                  <div className="p-3.5">
                    <h2 className="font-display text-[15px] font-bold tracking-[0.08em] text-platinum uppercase">
                      {s.label}
                    </h2>
                    <p className="mt-1.5 text-[12px] leading-relaxed text-platinum-dim">
                      {s.line}
                    </p>
                  </div>
                </Panel>
              </Link>
            ))}
          </div>

          <div className="flex flex-col gap-4">
            <Panel title="Local inference" delay={140}>
              <div className="divide-y divide-border">
                {(jarvis.data?.endpoints ?? []).map((e) => (
                  <div key={e.url} className="flex items-center justify-between gap-2 px-3 py-2.5">
                    <div>
                      <p className="font-display text-[12px] font-semibold text-platinum">{e.label}</p>
                      <p className="font-mono text-[10px] text-platinum-dim">{e.url}</p>
                    </div>
                    <StatusPill
                      tone={e.up ? "live" : "steel"}
                      label={e.up ? (e.models[0] ?? "loaded").slice(0, 18) : "down"}
                    />
                  </div>
                ))}
                {(jarvis.data?.endpoints ?? []).length === 0 && (
                  <p className="p-3 font-mono text-[11px] text-platinum-dim">probing…</p>
                )}
              </div>
            </Panel>

            <Panel
              title="Install on the unit"
              delay={160}
              right={
                <ControlButton
                  onClick={() => {
                    void navigator.clipboard?.writeText(INSTALL);
                    setCopied(true);
                    window.setTimeout(() => setCopied(false), 1400);
                  }}
                >
                  {copied ? "copied" : "copy"}
                </ControlButton>
              }
            >
              <pre className="scroll-thin overflow-x-auto p-3 font-mono text-[11px] leading-relaxed text-platinum-dim">
                {INSTALL}
              </pre>
            </Panel>
          </div>
        </div>
      </div>
    </Shell>
  );
}

export default Deck;
