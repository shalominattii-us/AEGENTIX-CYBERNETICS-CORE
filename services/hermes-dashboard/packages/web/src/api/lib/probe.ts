/**
 * Probes a Hermes Governor control API for reachability.
 *
 * The real governor runs on the operator's own unit (spec: port 9950; the
 * operator's current deployment answers on 9119), so from any other host the
 * probe is expected to fail — the dashboard then labels itself LOCAL and serves
 * seeded control-plane state instead of pretending to be live.
 */
export type GovernorLink = {
  endpoint: string;
  reachable: boolean;
  latencyMs: number | null;
  detail: string;
};

export async function probeGovernor(endpoint: string): Promise<GovernorLink> {
  const started = Date.now();
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 1500);
    const res = await fetch(`${endpoint.replace(/\/$/, "")}/health`, {
      signal: controller.signal,
    });
    clearTimeout(timer);
    return {
      endpoint,
      reachable: res.ok,
      latencyMs: Date.now() - started,
      detail: res.ok
        ? `governor responded ${res.status}`
        : `governor responded ${res.status}`,
    };
  } catch (err) {
    return {
      endpoint,
      reachable: false,
      latencyMs: null,
      detail:
        err instanceof Error && err.name === "AbortError"
          ? "probe timed out after 1500ms"
          : "no listener reachable from this host",
    };
  }
}
