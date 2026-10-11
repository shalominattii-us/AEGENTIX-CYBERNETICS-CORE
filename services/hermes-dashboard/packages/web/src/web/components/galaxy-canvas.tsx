import { useEffect, useMemo, useRef, useState } from "react";

export type GalaxyNode = {
  id: number;
  title: string;
  kind: string;
  cluster: string;
  mass: number;
};
export type GalaxyLink = { sourceId: number; targetId: number; relation: string };

type Placed = GalaxyNode & { x: number; y: number; r: number; hue: number };

const ARM_HUE: Record<string, number> = {
  "Sovereign Core": 205,
  SovereignOS: 190,
  AEGENTIX: 46,
  "Agent Mesh": 155,
  Cognition: 280,
  CyberGym: 12,
  "Outer Rim": 230,
};

function hueFor(cluster: string) {
  if (ARM_HUE[cluster] !== undefined) return ARM_HUE[cluster];
  let h = 0;
  for (const ch of cluster) h = (h * 31 + ch.charCodeAt(0)) % 360;
  return h;
}

/**
 * Lays nodes out as a logarithmic spiral galaxy: one arm per cluster, mass
 * driving radius, anchors (planets/agents) pulled toward the core.
 */
function layout(nodes: GalaxyNode[]): Placed[] {
  const clusters = [...new Set(nodes.map((n) => n.cluster))].sort();
  const perCluster = new Map<string, GalaxyNode[]>();
  for (const n of nodes) {
    if (!perCluster.has(n.cluster)) perCluster.set(n.cluster, []);
    perCluster.get(n.cluster)!.push(n);
  }

  const placed: Placed[] = [];
  clusters.forEach((cluster, ci) => {
    const members = perCluster.get(cluster)!;
    // anchors first, they sit closest to the galactic centre
    members.sort((a, b) => (a.kind === "star" ? 1 : 0) - (b.kind === "star" ? 1 : 0));
    const armOffset = (ci / clusters.length) * Math.PI * 2;

    members.forEach((n, i) => {
      const t = (i + 1) / (members.length + 1);
      const isAnchor = n.kind !== "star";
      // log spiral: radius grows, angle winds
      const radius = isAnchor ? 90 + t * 60 : 150 + Math.pow(t, 0.75) * 430;
      const wind = armOffset + t * 2.1 + (isAnchor ? 0 : 0.35);
      // deterministic jitter so arms look organic but stable across renders
      const jitter = Math.sin(n.id * 12.9898) * 26;
      const jitterA = Math.cos(n.id * 78.233) * 0.1;

      placed.push({
        ...n,
        x: Math.cos(wind + jitterA) * (radius + jitter),
        y: Math.sin(wind + jitterA) * (radius + jitter) * 0.62,
        r: (isAnchor ? 7 : 2.4) + n.mass * (isAnchor ? 1.6 : 0.85),
        hue: hueFor(n.cluster),
      });
    });
  });
  return placed;
}

export function GalaxyCanvas({
  nodes,
  links,
  selectedId,
  onSelect,
  filterCluster,
  query,
}: {
  nodes: GalaxyNode[];
  links: GalaxyLink[];
  selectedId: number | null;
  onSelect: (id: number) => void;
  filterCluster: string | null;
  query: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [view, setView] = useState({ x: 0, y: 0, zoom: 1 });
  const [hover, setHover] = useState<number | null>(null);
  const drag = useRef<{ x: number; y: number; vx: number; vy: number } | null>(null);
  const spin = useRef(0);

  const placed = useMemo(() => layout(nodes), [nodes]);
  const byId = useMemo(() => new Map(placed.map((p) => [p.id, p])), [placed]);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    return new Set(
      placed.filter((p) => p.title.toLowerCase().includes(q)).map((p) => p.id),
    );
  }, [placed, query]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let frame = 0;
    const render = () => {
      const dpr = window.devicePixelRatio || 1;
      const { clientWidth: w, clientHeight: h } = canvas;
      if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
        canvas.width = w * dpr;
        canvas.height = h * dpr;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);

      spin.current += 0.0004;

      ctx.save();
      ctx.translate(w / 2 + view.x, h / 2 + view.y);
      ctx.scale(view.zoom, view.zoom);
      ctx.rotate(spin.current);

      // galactic core glow
      const core = ctx.createRadialGradient(0, 0, 0, 0, 0, 240);
      core.addColorStop(0, "oklch(0.72 0.11 240 / 0.20)");
      core.addColorStop(0.5, "oklch(0.58 0.08 245 / 0.07)");
      core.addColorStop(1, "transparent");
      ctx.fillStyle = core;
      ctx.beginPath();
      ctx.arc(0, 0, 240, 0, Math.PI * 2);
      ctx.fill();

      const dim = (id: number) => {
        if (filterCluster && byId.get(id)?.cluster !== filterCluster) return true;
        if (matches && !matches.has(id)) return true;
        return false;
      };

      // edges
      for (const link of links) {
        const a = byId.get(link.sourceId);
        const b = byId.get(link.targetId);
        if (!a || !b) continue;
        const faded = dim(a.id) && dim(b.id);
        const active =
          selectedId !== null &&
          (link.sourceId === selectedId || link.targetId === selectedId);

        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        // curve edges toward the core for a swept, orbital look
        ctx.quadraticCurveTo((a.x + b.x) / 2 * 0.72, (a.y + b.y) / 2 * 0.72, b.x, b.y);
        ctx.strokeStyle = active
          ? `oklch(0.82 0.14 ${a.hue} / 0.75)`
          : faded
            ? "oklch(0.58 0.08 245 / 0.04)"
            : link.relation === "wikilink"
              ? `oklch(0.7 0.1 ${a.hue} / 0.28)`
              : "oklch(0.58 0.08 245 / 0.10)";
        ctx.lineWidth = active ? 1.4 : 0.6;
        ctx.stroke();
      }

      // bodies
      for (const p of placed) {
        const faded = dim(p.id);
        const isSel = p.id === selectedId;
        const isHover = p.id === hover;
        const alpha = faded ? 0.12 : 1;

        if (!faded && (p.kind !== "star" || isSel || isHover)) {
          const glow = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.r * 6);
          glow.addColorStop(0, `oklch(0.8 0.15 ${p.hue} / ${isSel ? 0.5 : 0.26})`);
          glow.addColorStop(1, "transparent");
          ctx.fillStyle = glow;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r * 6, 0, Math.PI * 2);
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, isSel || isHover ? p.r * 1.5 : p.r, 0, Math.PI * 2);
        ctx.fillStyle =
          p.kind === "star"
            ? `oklch(0.9 0.05 ${p.hue} / ${alpha})`
            : `oklch(0.82 0.16 ${p.hue} / ${alpha})`;
        ctx.fill();

        if (isSel) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.r * 3.2, 0, Math.PI * 2);
          ctx.strokeStyle = `oklch(0.9 0.12 ${p.hue} / 0.8)`;
          ctx.lineWidth = 1;
          ctx.stroke();
        }

        // labels for anchors, selection, hover, and search hits
        const labelled =
          !faded &&
          (p.kind !== "star" || isSel || isHover || (matches?.has(p.id) ?? false));
        if (labelled && view.zoom > 0.45) {
          ctx.save();
          ctx.translate(p.x, p.y);
          ctx.rotate(-spin.current);
          ctx.font =
            p.kind === "star"
              ? "500 9px 'JetBrains Mono', monospace"
              : "600 11px 'Chakra Petch', sans-serif";
          ctx.fillStyle = isSel
            ? "oklch(0.96 0.01 250)"
            : `oklch(0.86 0.02 250 / ${p.kind === "star" ? 0.75 : 0.95})`;
          ctx.textAlign = "center";
          ctx.fillText(
            p.kind === "star" ? p.title : p.title.toUpperCase(),
            0,
            -p.r * 2.4,
          );
          ctx.restore();
        }
      }

      ctx.restore();
      frame = requestAnimationFrame(render);
    };
    frame = requestAnimationFrame(render);
    return () => cancelAnimationFrame(frame);
  }, [placed, links, byId, view, selectedId, hover, filterCluster, matches]);

  /** Screen point -> nearest body, accounting for pan, zoom, and slow spin. */
  const pick = (clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const px = clientX - rect.left - rect.width / 2 - view.x;
    const py = clientY - rect.top - rect.height / 2 - view.y;
    const zx = px / view.zoom;
    const zy = py / view.zoom;
    const cos = Math.cos(-spin.current);
    const sin = Math.sin(-spin.current);
    const wx = zx * cos - zy * sin;
    const wy = zx * sin + zy * cos;

    let best: Placed | null = null;
    let bestDist = Infinity;
    for (const p of placed) {
      const d = Math.hypot(p.x - wx, p.y - wy);
      const hitR = Math.max(9, p.r * 2.4);
      if (d < hitR && d < bestDist) {
        best = p;
        bestDist = d;
      }
    }
    return best;
  };

  return (
    <canvas
      ref={canvasRef}
      aria-label="Galaxy map — drag to pan, wheel to zoom, click a body"
      className="h-full w-full cursor-crosshair touch-none"
      onMouseDown={(e) => {
        drag.current = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y };
      }}
      onMouseUp={(e) => {
        const moved =
          drag.current &&
          Math.hypot(e.clientX - drag.current.x, e.clientY - drag.current.y) > 4;
        if (!moved) {
          const hit = pick(e.clientX, e.clientY);
          if (hit) onSelect(hit.id);
        }
        drag.current = null;
      }}
      onMouseLeave={() => {
        drag.current = null;
        setHover(null);
      }}
      onMouseMove={(e) => {
        if (drag.current) {
          setView((v) => ({
            ...v,
            x: drag.current!.vx + (e.clientX - drag.current!.x),
            y: drag.current!.vy + (e.clientY - drag.current!.y),
          }));
          return;
        }
        const hit = pick(e.clientX, e.clientY);
        setHover(hit?.id ?? null);
      }}
      onWheel={(e) => {
        e.preventDefault();
        setView((v) => ({
          ...v,
          zoom: Math.min(4, Math.max(0.25, v.zoom * (e.deltaY > 0 ? 0.9 : 1.1))),
        }));
      }}
    />
  );
}
