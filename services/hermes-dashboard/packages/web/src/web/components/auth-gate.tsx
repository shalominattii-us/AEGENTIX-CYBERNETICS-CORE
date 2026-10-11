import { useEffect, useState } from "react";
import { authClient } from "../lib/auth";
import { useAccess } from "../queries/access";
import { ControlButton, Panel, StatusPill } from "./instruments";

/**
 * The console's front door. Every procedure behind it is session-gated on the
 * server, so this is a UX gate rather than the security boundary — the API
 * rejects unauthenticated calls regardless of what the client renders.
 */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { data: session, isPending } = authClient.useSession();
  const [settling, setSettling] = useState(true);
  const access = useAccess(Boolean(session));

  // Completes a returning managed sign-in (the top-level redirect leg).
  useEffect(() => {
    let alive = true;
    void authClient.managedAuth
      .handleRedirect()
      .catch(() => undefined)
      .finally(() => {
        if (alive) setSettling(false);
      });
    return () => {
      alive = false;
    };
  }, []);

  if (isPending || settling) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-obsidian">
        <div className="font-mono text-xs tracking-[0.3em] text-steel uppercase">
          resolving operator…
        </div>
      </div>
    );
  }

  if (!session) return <SignIn />;
  if (access.isPending) return <div className="p-10 font-mono text-steel">Checking owner authorization…</div>;
  if (!access.data?.authorized) {
    return (
      <div className="mx-auto max-w-lg space-y-5 p-10">
        <StatusPill tone="armed" label="owner binding required" />
        <h1 className="font-display text-3xl text-platinum">Identity verified. Controls locked.</h1>
        <p className="text-steel">Signing in does not grant ownership. The deployment administrator must bind your verified user ID through the server configuration. No email address is assumed and no first-signup takeover is allowed.</p>
        <p className="break-all font-mono text-xs text-platinum">Your identity ID: {access.data?.identityId ?? "unavailable"}</p>
        <p className="font-mono text-xs text-steel">Server setting: HERMES_OWNER_USER_ID</p>
        <ControlButton onClick={() => { void authClient.signOut(); }}>Sign out</ControlButton>
      </div>
    );
  }

  return <>{children}</>;
}

function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<null | "google" | "local">(null);

  async function google() {
    setError(null);
    setBusy("google");
    const result = await authClient.managedAuth.signIn({ provider: "google" });
    if (result.error && result.error.code !== "POPUP_CLOSED") {
      setError(result.error.message ?? "Sign-in failed.");
    }
    setBusy(null);
  }

  async function local(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy("local");
    const result = await authClient.signIn.email({ email, password });
    if (result.error) setError(result.error.message ?? "Sign-in failed.");
    setBusy(null);
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-obsidian px-6 py-16">
      {/* Layered field so the gate reads like part of the console, not a form page. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(233,237,243,.6) 1px, transparent 1px), linear-gradient(90deg, rgba(233,237,243,.6) 1px, transparent 1px)",
          backgroundSize: "72px 72px",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-40 left-1/2 h-[42rem] w-[42rem] -translate-x-1/2 rounded-full opacity-25 blur-3xl"
        style={{ background: "radial-gradient(circle, #1f6feb 0%, transparent 65%)" }}
      />

      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mb-4 flex justify-center">
            <StatusPill tone="live" label="sovereign" />
          </div>
          <h1 className="font-display text-4xl font-semibold tracking-tight text-platinum">
            Hermes Console
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-steel">
            Governor controls, corpus galaxy and shared memory sit behind this gate.
            Authenticate to take the operator seat.
          </p>
        </div>

        <Panel>
          <div className="space-y-5">
            <ControlButton
              tone="live"
              className="w-full justify-center py-2.5"
              disabled={busy !== null}
              onClick={google}
            >
              {busy === "google" ? "opening provider…" : "Continue with Google"}
            </ControlButton>

            <div className="flex items-center gap-3">
              <div className="h-px flex-1 bg-steel/20" />
              <span className="font-mono text-[10px] tracking-[0.25em] text-steel uppercase">
                or local operator
              </span>
              <div className="h-px flex-1 bg-steel/20" />
            </div>

            <form onSubmit={local} className="space-y-3">
              <label className="block">
                <span className="mb-1.5 block font-mono text-[10px] tracking-[0.2em] text-steel uppercase">
                  email
                </span>
                <input
                  aria-label="Operator email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  autoComplete="email"
                  className="w-full rounded-md border border-steel/25 bg-obsidian/60 px-3 py-2 font-mono text-sm text-platinum outline-none placeholder:text-steel/50 focus:border-live"
                  placeholder="operator@unit.local"
                />
              </label>
              <label className="block">
                <span className="mb-1.5 block font-mono text-[10px] tracking-[0.2em] text-steel uppercase">
                  passphrase
                </span>
                <input
                  aria-label="Operator passphrase"
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  className="w-full rounded-md border border-steel/25 bg-obsidian/60 px-3 py-2 font-mono text-sm text-platinum outline-none placeholder:text-steel/50 focus:border-live"
                  placeholder="••••••••"
                />
              </label>

              <button
                type="submit"
                disabled={busy !== null}
                className="w-full rounded-md border border-live/40 bg-live/10 px-4 py-2.5 font-mono text-xs tracking-[0.2em] text-live uppercase transition hover:bg-live/20 disabled:opacity-40"
              >
                {busy === "local"
                  ? "authenticating…"
                  : "take the seat"}
              </button>
            </form>

            {error && (
              <div className="rounded-md border border-breach/40 bg-breach/10 px-3 py-2 font-mono text-xs text-breach">
                {error}
              </div>
            )}

            <p className="text-center font-mono text-[11px] text-steel">Public password signup is disabled. Verified sign-in still requires owner authorization.</p>
          </div>
        </Panel>

        <p className="mt-6 text-center font-mono text-[10px] leading-relaxed tracking-wide text-steel/70 uppercase">
          model endpoints are configured separately · credentials never belong in shared memory
        </p>
      </div>
    </div>
  );
}
