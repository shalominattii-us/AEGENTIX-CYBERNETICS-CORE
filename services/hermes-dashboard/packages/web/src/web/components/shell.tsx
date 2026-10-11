import { useState, type ReactNode } from "react";
import { Link, useLocation } from "wouter";
import { cn } from "@/lib/utils";
import { StatusPill, modeTone } from "./instruments";
import { useSnapshot } from "../queries/governor";
import { useJarvisStatus } from "../queries/galaxy";
import { authClient } from "../lib/auth";

const NAV = [
  { href: "/", label: "Deck" },
  { href: "/governor", label: "Governor" },
  { href: "/galaxy", label: "Galaxy" },
  { href: "/notebook", label: "Notebook" },
  { href: "/jarvis", label: "Jarvis" },
];

/** Persistent frame: identity, navigation, and the two posture readouts. */
export function Shell({ children, flush }: { children: ReactNode; flush?: boolean }) {
  const [path] = useLocation();
  const snapshot = useSnapshot();
  const jarvis = useJarvisStatus();

  const state = snapshot.data?.state;
  const link = snapshot.data?.link;

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <header className="flex shrink-0 flex-wrap items-center gap-x-6 gap-y-2 border-b border-border bg-obsidian/80 px-4 py-2.5 backdrop-blur">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="font-display text-[15px] font-bold tracking-[0.1em] text-platinum uppercase">
            Hermes
          </span>
          <span className="font-mono text-[10px] tracking-[0.18em] text-platinum-dim uppercase">
            sovereign control plane
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          {NAV.map((item) => {
            const active = item.href === "/" ? path === "/" : path.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors",
                  active
                    ? "border-steel-bright/70 bg-steel/15 text-platinum"
                    : "border-transparent text-platinum-dim hover:border-border hover:text-platinum",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <StatusPill
            tone={jarvis.data?.online ? "live" : "steel"}
            label={
              jarvis.data?.online
                ? `jarvis ${(jarvis.data.activeModel ?? "local").slice(0, 22)}`
                : "jarvis offline"
            }
          />
          <StatusPill
            tone={link?.reachable ? "live" : "breach"}
            label={link?.reachable ? "governor link" : "link local"}
          />
          <StatusPill
            tone={state ? modeTone(state.mode) : "steel"}
            label={state?.mode ?? "…"}
            pulse={state?.mode === "live"}
          />
          {state?.killSwitchEngaged && <StatusPill tone="breach" label="kill engaged" />}
          <OperatorChip />
        </div>
      </header>

      <main className={cn("min-h-0 flex-1", flush ? "overflow-hidden" : "overflow-y-auto scroll-thin")}>
        {children}
      </main>
    </div>
  );
}

/** Signed-in operator + sign-out, pinned to the right of the status rail. */
function OperatorChip() {
  const { data: session } = authClient.useSession();
  const [busy, setBusy] = useState(false);
  if (!session) return null;

  const who = session.user.name || session.user.email || "operator";

  return (
    <div className="ml-1 flex items-center gap-2 border-l border-steel/20 pl-3">
      <span
        title={session.user.email ?? who}
        className="max-w-[10rem] truncate font-mono text-[11px] text-steel"
      >
        {who}
      </span>
      <button
        type="button"
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          await authClient.signOut();
          setBusy(false);
        }}
        className="rounded border border-steel/25 px-2 py-1 font-mono text-[10px] tracking-[0.18em] text-steel uppercase transition hover:border-breach/50 hover:text-breach disabled:opacity-40"
      >
        {busy ? "…" : "out"}
      </button>
    </div>
  );
}
