import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export type Tone = "live" | "armed" | "breach" | "steel";

const TONE_TEXT: Record<Tone, string> = {
  live: "text-live",
  armed: "text-armed",
  breach: "text-breach",
  steel: "text-platinum-dim",
};
const TONE_BG: Record<Tone, string> = {
  live: "bg-live",
  armed: "bg-armed",
  breach: "bg-breach",
  steel: "bg-steel",
};

/** dot + uppercase mono label, colored by state token. */
export function StatusPill({
  tone,
  label,
  pulse,
  className,
}: {
  tone: Tone;
  label: string;
  pulse?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 border border-border bg-obsidian/60 px-2 py-1",
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", TONE_BG[tone], pulse && "animate-pulse")} />
      <span
        className={cn(
          "font-mono text-[10px] font-medium uppercase tracking-[0.14em]",
          TONE_TEXT[tone],
        )}
      >
        {label}
      </span>
    </span>
  );
}

export function Panel({
  title,
  right,
  children,
  className,
  delay = 0,
}: {
  title?: string;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  return (
    <section
      className={cn("panel animate-rise flex flex-col", className)}
      style={{ animationDelay: `${delay}ms` }}
    >
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-border px-3 py-2">
          <h2 className="panel-title">{title}</h2>
          {right}
        </header>
      )}
      <div className="flex min-h-0 flex-1 flex-col">{children}</div>
    </section>
  );
}

export function Metric({
  label,
  value,
  unit,
  tone = "steel",
  sub,
}: {
  label: string;
  value: string;
  unit?: string;
  tone?: Tone;
  sub?: string;
}) {
  return (
    <div className="px-3 py-3">
      <p className="data-label">{label}</p>
      <p className="mt-1 flex items-baseline gap-1.5">
        <span className={cn("font-mono text-[28px] leading-none font-medium", TONE_TEXT[tone])}>
          {value}
        </span>
        {unit && <span className="font-mono text-[11px] text-platinum-dim">{unit}</span>}
      </p>
      {sub && <p className="mt-1.5 font-mono text-[10px] text-platinum-dim">{sub}</p>}
    </div>
  );
}

export function LimitBar({ consumed, ceiling }: { consumed: number; ceiling: number }) {
  const ratio = ceiling > 0 ? Math.min(1, consumed / ceiling) : 0;
  const tone: Tone = ratio >= 1 ? "breach" : ratio >= 0.75 ? "armed" : "live";
  return (
    <div className="h-1 w-full bg-obsidian">
      <div
        className={cn("h-full transition-all duration-500", TONE_BG[tone])}
        style={{ width: `${Math.max(2, ratio * 100)}%` }}
      />
    </div>
  );
}

export function verdictTone(verdict: string): Tone {
  if (verdict === "allow" || verdict === "arm") return "live";
  if (verdict === "override") return "armed";
  if (verdict === "deny" || verdict === "halt") return "breach";
  return "steel";
}

export function modeTone(mode: string): Tone {
  if (mode === "live") return "live";
  if (mode === "armed") return "armed";
  return "breach";
}

export function ControlButton({
  children,
  onClick,
  tone = "steel",
  disabled,
  className,
}: {
  children: ReactNode;
  onClick: () => void;
  tone?: Tone;
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        "border px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors disabled:cursor-not-allowed disabled:opacity-40",
        tone === "breach"
          ? "border-breach/60 text-breach hover:bg-breach/15"
          : tone === "live"
            ? "border-live/60 text-live hover:bg-live/15"
            : tone === "armed"
              ? "border-armed/60 text-armed hover:bg-armed/15"
              : "border-border text-platinum-dim hover:border-steel-bright hover:text-platinum",
        className,
      )}
    >
      {children}
    </button>
  );
}

export function fmtUsd(value: number) {
  const sign = value < 0 ? "-" : "";
  return `${sign}$${Math.abs(value).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function fmtTime(value: string | number | Date) {
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "—" : d.toISOString().slice(0, 19).replace("T", " ");
}
