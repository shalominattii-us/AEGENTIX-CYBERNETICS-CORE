import type { ReactNode } from "react";

/**
 * Deliberately tiny markdown renderer — no dependency, no remote fetch.
 * Supports headings, bullets, fenced code, inline code, bold, and
 * [[wikilinks]] (routed back into the galaxy via onWikilink).
 */

function inline(text: string, onWikilink?: (slug: string) => void): ReactNode[] {
  const out: ReactNode[] = [];
  const pattern = /(\[\[[^\]]+\]\]|`[^`]+`|\*\*[^*]+\*\*)/g;
  let last = 0;
  let key = 0;
  for (const match of text.matchAll(pattern)) {
    const at = match.index ?? 0;
    if (at > last) out.push(text.slice(last, at));
    const token = match[0];
    if (token.startsWith("[[")) {
      const label = token.slice(2, -2);
      out.push(
        <button
          key={`w${key++}`}
          type="button"
          onClick={() => onWikilink?.(label)}
          className="font-mono text-[0.95em] text-steel-bright underline decoration-steel/50 underline-offset-2 hover:text-platinum"
        >
          {label}
        </button>,
      );
    } else if (token.startsWith("`")) {
      out.push(
        <code
          key={`c${key++}`}
          className="bg-obsidian-raised px-1 py-0.5 font-mono text-[0.9em] text-platinum"
        >
          {token.slice(1, -1)}
        </code>,
      );
    } else {
      out.push(
        <strong key={`b${key++}`} className="font-semibold text-platinum">
          {token.slice(2, -2)}
        </strong>,
      );
    }
    last = at + token.length;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

export function Markdown({
  source,
  onWikilink,
  className,
}: {
  source: string;
  onWikilink?: (slug: string) => void;
  className?: string;
}) {
  const lines = source.split("\n");
  const blocks: ReactNode[] = [];
  let bullets: string[] = [];
  let fence: string[] | null = null;

  const flushBullets = () => {
    if (bullets.length === 0) return;
    blocks.push(
      <ul key={`u${blocks.length}`} className="my-2 space-y-1 pl-4">
        {bullets.map((b, i) => (
          <li key={i} className="list-disc text-[13px] leading-relaxed text-platinum-dim">
            {inline(b, onWikilink)}
          </li>
        ))}
      </ul>,
    );
    bullets = [];
  };

  for (const line of lines) {
    if (line.trimStart().startsWith("```")) {
      if (fence) {
        blocks.push(
          <pre
            key={`f${blocks.length}`}
            className="my-2 overflow-x-auto border border-border bg-obsidian p-3 font-mono text-[12px] text-platinum-dim"
          >
            {fence.join("\n")}
          </pre>,
        );
        fence = null;
      } else {
        flushBullets();
        fence = [];
      }
      continue;
    }
    if (fence) {
      fence.push(line);
      continue;
    }

    const heading = /^(#{1,4})\s+(.*)$/.exec(line);
    if (heading) {
      flushBullets();
      const level = heading[1].length;
      blocks.push(
        <p
          key={`h${blocks.length}`}
          className={
            level <= 2
              ? "mt-4 mb-1 font-display text-[13px] font-bold uppercase tracking-[0.12em] text-platinum"
              : "mt-3 mb-1 font-display text-[11px] font-semibold uppercase tracking-[0.14em] text-platinum-dim"
          }
        >
          {inline(heading[2], onWikilink)}
        </p>,
      );
      continue;
    }

    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
    if (bullet) {
      bullets.push(bullet[1]);
      continue;
    }

    if (line.trim() === "") {
      flushBullets();
      continue;
    }

    flushBullets();
    blocks.push(
      <p key={`p${blocks.length}`} className="my-1.5 text-[13px] leading-relaxed text-platinum-dim">
        {inline(line, onWikilink)}
      </p>,
    );
  }
  flushBullets();
  if (fence) {
    blocks.push(
      <pre
        key="ftail"
        className="my-2 overflow-x-auto border border-border bg-obsidian p-3 font-mono text-[12px] text-platinum-dim"
      >
        {fence.join("\n")}
      </pre>,
    );
  }

  return <div className={className}>{blocks}</div>;
}
