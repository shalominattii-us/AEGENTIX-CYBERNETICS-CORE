import { useEffect, useState } from "react";
import { Shell } from "../components/shell";
import {
  ControlButton,
  LimitBar,
  Metric,
  Panel,
  StatusPill,
  fmtTime,
  fmtUsd,
  modeTone,
  verdictTone,
} from "../components/instruments";
import {
  useAudit,
  useResetWindow,
  useSetEndpoint,
  useSetKillSwitch,
  useSetLimitEnforced,
  useSetMode,
  useSetProofGate,
  useSnapshot,
} from "../queries/governor";

function GovernorConsole() {
  const snapshot = useSnapshot();
  const audit = useAudit(60);

  const setKill = useSetKillSwitch();
  const setMode = useSetMode();
  const setGate = useSetProofGate();
  const setEndpoint = useSetEndpoint();
  const setEnforced = useSetLimitEnforced();
  const resetWindow = useResetWindow();

  const [armKill, setArmKill] = useState(false);
  const [pulse, setPulse] = useState(false);
  const [endpointDraft, setEndpointDraft] = useState("");
  const [denied, setDenied] = useState<string | null>(null);

  const state = snapshot.data?.state;
  const limits = snapshot.data?.limits ?? [];
  const positions = snapshot.data?.positions ?? [];
  const totals = snapshot.data?.totals;
  const link = snapshot.data?.link;

  useEffect(() => {
    if (state && endpointDraft === "") setEndpointDraft(state.endpoint);
  }, [state, endpointDraft]);

  const firePulse = () => {
    setPulse(true);
    window.setTimeout(() => setPulse(false), 420);
  };

  const requestMode = (mode: "halted" | "armed" | "live") => {
    setDenied(null);
    setMode.mutate(
      { mode, reason: `operator set mode ${mode} from console` },
      {
        onSuccess: (res) => {
          if (!res.ok) {
            setDenied(res.denied ?? "DENIED");
            firePulse();
          }
        },
      },
    );
  };

  return (
    <Shell>
      <div
        className={`grid gap-4 p-4 xl:grid-cols-[300px_minmax(0,1fr)_360px] ${
          pulse ? "animate-frame-pulse" : ""
        }`}
      >
        {/* ---------------- status rail ---------------- */}
        <div className="flex flex-col gap-4">
          <Panel title="Posture">
            <div className="divide-y divide-border">
              <div className="flex items-center justify-between px-3 py-2.5">
                <span className="data-label">Mode</span>
                <StatusPill
                  tone={state ? modeTone(state.mode) : "steel"}
                  label={state?.mode ?? "…"}
                  pulse={state?.mode === "live"}
                />
              </div>
              <div className="flex items-center justify-between px-3 py-2.5">
                <span className="data-label">Kill switch</span>
                <StatusPill
                  tone={state?.killSwitchEngaged ? "breach" : "live"}
                  label={state?.killSwitchEngaged ? "engaged" : "released"}
                />
              </div>
              <div className="flex items-center justify-between px-3 py-2.5">
                <span className="data-label">Paper-proof gate</span>
                <StatusPill
                  tone={state?.paperProofGate ? "armed" : "live"}
                  label={state?.paperProofGate ? "closed" : "cleared"}
                />
              </div>
              <div className="flex items-center justify-between px-3 py-2.5">
                <span className="data-label">Breaches</span>
                <span
                  className={`font-mono text-[13px] ${
                    (totals?.breaches ?? 0) > 0 ? "text-breach" : "text-live"
                  }`}
                >
                  {totals?.breaches ?? 0}
                </span>
              </div>
            </div>
          </Panel>

          <Panel title="Mode control" delay={40}>
            <div className="flex flex-col gap-2 p-3">
              <div className="flex gap-2">
                <ControlButton tone="breach" onClick={() => requestMode("halted")}>
                  Halt
                </ControlButton>
                <ControlButton tone="armed" onClick={() => requestMode("armed")}>
                  Arm
                </ControlButton>
                <ControlButton tone="live" onClick={() => requestMode("live")}>
                  Go live
                </ControlButton>
              </div>
              {denied && (
                <p className="font-mono text-[10px] leading-relaxed text-breach uppercase">
                  denied — {denied.replace(/_/g, " ").toLowerCase()}
                </p>
              )}
              <div className="hairline mt-1 pt-3">
                <p className="data-label mb-2">Paper-proof gate</p>
                <div className="flex gap-2">
                  <ControlButton
                    tone="armed"
                    disabled={!state || state.paperProofGate}
                    onClick={() =>
                      setGate.mutate({
                        gated: true,
                        reason: "operator re-armed the paper-proof gate",
                      })
                    }
                  >
                    Close gate
                  </ControlButton>
                  <ControlButton
                    tone="steel"
                    disabled={!state || !state.paperProofGate}
                    onClick={() =>
                      setGate.mutate({
                        gated: false,
                        reason: "paper-proof reviewed and accepted by operator",
                      })
                    }
                  >
                    Clear gate
                  </ControlButton>
                </div>
              </div>
            </div>
          </Panel>

          <Panel title="Kill switch" delay={80}>
            <div className="flex flex-col gap-2 p-3">
              {state?.killSwitchEngaged ? (
                <>
                  <p className="font-mono text-[10px] leading-relaxed text-platinum-dim uppercase">
                    all execution halted at the governor
                  </p>
                  {armKill ? (
                    <div className="flex gap-2">
                      <ControlButton
                        tone="live"
                        onClick={() => {
                          setKill.mutate({
                            engaged: false,
                            reason: "operator released kill switch after review",
                          });
                          setArmKill(false);
                        }}
                      >
                        Confirm release
                      </ControlButton>
                      <ControlButton tone="steel" onClick={() => setArmKill(false)}>
                        Cancel
                      </ControlButton>
                    </div>
                  ) : (
                    <ControlButton tone="steel" onClick={() => setArmKill(true)}>
                      Release kill switch
                    </ControlButton>
                  )}
                </>
              ) : (
                <>
                  <p className="font-mono text-[10px] leading-relaxed text-platinum-dim uppercase">
                    execution permitted within policy
                  </p>
                  {armKill ? (
                    <div className="flex gap-2">
                      <ControlButton
                        tone="breach"
                        onClick={() => {
                          setKill.mutate({
                            engaged: true,
                            reason: "operator engaged kill switch from console",
                          });
                          setArmKill(false);
                          firePulse();
                        }}
                      >
                        Confirm halt
                      </ControlButton>
                      <ControlButton tone="steel" onClick={() => setArmKill(false)}>
                        Cancel
                      </ControlButton>
                    </div>
                  ) : (
                    <ControlButton tone="breach" onClick={() => setArmKill(true)}>
                      Engage kill switch
                    </ControlButton>
                  )}
                </>
              )}
            </div>
          </Panel>
        </div>

        {/* ---------------- primary telemetry ---------------- */}
        <div className="flex min-w-0 flex-col gap-4">
          <Panel
            title="Control link"
            delay={40}
            right={
              <StatusPill
                tone={link?.reachable ? "live" : "breach"}
                label={link?.reachable ? `live ${link.latencyMs}ms` : "local state"}
              />
            }
          >
            <div className="flex flex-wrap items-center gap-2 p-3">
              <input
                value={endpointDraft}
                onChange={(e) => setEndpointDraft(e.target.value)}
                spellCheck={false}
                aria-label="Hermes Governor endpoint"
                className="min-w-[240px] flex-1 border border-border bg-obsidian px-2.5 py-1.5 font-mono text-[12px] text-platinum outline-none focus:border-steel-bright"
              />
              <ControlButton
                onClick={() => setEndpoint.mutate({ endpoint: endpointDraft.trim() })}
                disabled={!endpointDraft.trim() || endpointDraft === state?.endpoint}
              >
                Point governor
              </ControlButton>
              <p className="w-full font-mono text-[10px] text-platinum-dim">
                {link?.detail ?? "probing…"} — spec default is{" "}
                <span className="text-steel-bright">:9950</span>, this deployment answers on{" "}
                <span className="text-steel-bright">:9119</span> on the unit. Unreachable means the
                console serves seeded local state, labelled LOCAL, and never claims to be live.
              </p>
            </div>
          </Panel>

          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Panel delay={80}>
              <Metric
                label="Exposure"
                value={totals ? fmtUsd(totals.exposureUsd) : "—"}
                sub={`${positions.length} positions`}
              />
            </Panel>
            <Panel delay={100}>
              <Metric
                label="Unrealised"
                value={totals ? fmtUsd(totals.unrealizedUsd) : "—"}
                tone={(totals?.unrealizedUsd ?? 0) >= 0 ? "live" : "breach"}
                sub="mark minus cost"
              />
            </Panel>
            <Panel delay={120}>
              <Metric
                label="Ledger"
                value={state?.paperProofGate ? "PAPER" : "LIVE"}
                tone={state?.paperProofGate ? "armed" : "live"}
                sub={state?.paperProofGate ? "proof gate closed" : "proof gate cleared"}
              />
            </Panel>
            <Panel delay={140}>
              <Metric
                label="Last change"
                value={state ? fmtTime(state.updatedAt).slice(11) : "—"}
                sub={state ? fmtTime(state.updatedAt).slice(0, 10) : undefined}
              />
            </Panel>
          </div>

          <Panel
            title="Policy limits"
            delay={160}
            right={
              <ControlButton onClick={() => resetWindow.mutate({})}>Reset window</ControlButton>
            }
          >
            <div className="divide-y divide-border">
              {limits.map((limit) => {
                const ratio = limit.ceiling > 0 ? limit.consumed / limit.ceiling : 0;
                return (
                  <div key={limit.id} className="px-3 py-2.5">
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="font-display text-[12px] font-semibold tracking-wide text-platinum">
                        {limit.name}
                      </span>
                      <span className="font-mono text-[11px] text-platinum-dim">
                        <span
                          className={
                            ratio >= 1
                              ? "text-breach"
                              : ratio >= 0.75
                                ? "text-armed"
                                : "text-platinum"
                          }
                        >
                          {limit.consumed.toLocaleString("en-US")}
                        </span>
                        {" / "}
                        {limit.ceiling.toLocaleString("en-US")} {limit.unit} · {limit.window}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-3">
                      <div className="flex-1">
                        <LimitBar consumed={limit.consumed} ceiling={limit.ceiling} />
                      </div>
                      <button
                        type="button"
                        onClick={() =>
                          setEnforced.mutate({ id: limit.id, enforced: !limit.enforced })
                        }
                        className={`font-mono text-[10px] uppercase tracking-[0.14em] ${
                          limit.enforced ? "text-live" : "text-armed"
                        }`}
                      >
                        {limit.enforced ? "enforced" : "suspended"}
                      </button>
                    </div>
                  </div>
                );
              })}
              {limits.length === 0 && (
                <p className="p-3 font-mono text-[11px] text-platinum-dim">loading limits…</p>
              )}
            </div>
          </Panel>

          <Panel title="Positions" delay={180}>
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  {["Asset", "Venue", "Qty", "Mark", "Value", "P/L", "Ledger"].map((h) => (
                    <th key={h} className="data-label px-3 py-2 text-left font-normal">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {positions.map((p) => {
                  const value = p.quantity * p.markUsd;
                  const pl = value - p.costUsd;
                  return (
                    <tr key={p.id} className="border-b border-border/60 last:border-0">
                      <td className="px-3 py-2 font-display text-[12px] font-semibold text-platinum">
                        {p.asset}
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px] text-platinum-dim">
                        {p.venue}
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px] text-platinum">
                        {p.quantity}
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px] text-platinum-dim">
                        {fmtUsd(p.markUsd)}
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px] text-platinum">
                        {fmtUsd(value)}
                      </td>
                      <td
                        className={`px-3 py-2 font-mono text-[11px] ${
                          pl >= 0 ? "text-live" : "text-breach"
                        }`}
                      >
                        {fmtUsd(pl)}
                      </td>
                      <td className="px-3 py-2">
                        <StatusPill
                          tone={p.ledger === "live" ? "live" : "armed"}
                          label={p.ledger}
                        />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </Panel>
        </div>

        {/* ---------------- audit stream ---------------- */}
        <Panel
          title="Audit trail"
          delay={200}
          className="max-h-[calc(100dvh-7rem)] xl:sticky xl:top-4"
        >
          <div className="scroll-thin min-h-0 flex-1 divide-y divide-border overflow-y-auto">
            {(audit.data ?? []).map((row) => (
              <div key={row.id} className="px-3 py-2.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-[10px] text-platinum-dim">
                    {fmtTime(row.at)}
                  </span>
                  <StatusPill tone={verdictTone(row.verdict)} label={row.verdict} />
                </div>
                <p className="mt-1.5 font-mono text-[11px] text-platinum">{row.subject}</p>
                <p className="mt-0.5 text-[12px] leading-snug text-platinum-dim">
                  {row.reason}
                </p>
                <p className="mt-1 font-mono text-[10px] text-steel">{row.actor}</p>
              </div>
            ))}
            {(audit.data ?? []).length === 0 && (
              <p className="p-3 font-mono text-[11px] text-platinum-dim">no decisions recorded</p>
            )}
          </div>
        </Panel>
      </div>
    </Shell>
  );
}

export default GovernorConsole;
