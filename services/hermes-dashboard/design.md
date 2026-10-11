# Hermes Governor — Design System

Operator console for the AEGENTIX treasury/trading control plane. Reads as an
instrument panel, not a marketing page: dense, monospaced telemetry, hard edges,
status-first hierarchy.

## Aesthetic direction

Sovereign obsidian ops console. Near-black substrate with a faint blueprint grid,
steel-blue structural lines, platinum type, and a single hot accent reserved for
armed/breach states. Nothing decorative — every color carries state meaning.

## Color

| Token | Value | Use |
|---|---|---|
| `--obsidian` | `oklch(0.16 0.012 250)` | page substrate |
| `--obsidian-raised` | `oklch(0.21 0.014 250)` | panel fill |
| `--steel` | `oklch(0.58 0.08 245)` | structural lines, borders, secondary data |
| `--steel-bright` | `oklch(0.72 0.11 240)` | active structural, links, focus ring |
| `--platinum` | `oklch(0.94 0.005 250)` | primary readouts |
| `--platinum-dim` | `oklch(0.68 0.008 250)` | labels, units, meta |
| `--live` | `oklch(0.76 0.17 155)` | healthy / within policy / connected |
| `--armed` | `oklch(0.80 0.16 85)` | armed, paper-gated, approaching limit |
| `--breach` | `oklch(0.63 0.22 25)` | kill-switch engaged, policy breach, disconnected |

Accent rule: `--breach` never appears unless something is actually wrong or halted.

## Typography

- **Display / headings:** `Chakra Petch` (600/700) — squared technical face, uppercase with `0.12em` tracking for panel titles.
- **Body / UI:** `Inter Tight` (400/500) — compact sans for prose and controls.
- **Data / numerals:** `JetBrains Mono` (400/500/700) — every number, hash, address, port, and timestamp. Tabular numerals so columns don't jitter.

Hierarchy: panel title 11px uppercase tracked, metric value 28–40px mono, label 10px uppercase dim.

## Layout

- Full-bleed dark canvas, 16px outer gutter, no centered max-width card stack.
- Asymmetric 12-column grid: status rail (left, narrow, sticky), primary telemetry (wide center), audit stream (right column, scrolls independently).
- Panels are 1px `--steel` bordered rectangles with 0 radius at the outer frame, `2px` radius inside. Hairline dividers, not shadows.
- Controlled density: tight 8/12/16px rhythm inside panels, generous 24px between panel groups.

## Backgrounds

Layered: obsidian base → 48px blueprint grid at 4% steel → subtle radial vignette
toward the top-left where the status rail sits. No gradient meshes, no glow blur.

## Motion

One orchestrated load: status rail fades/slides in first, telemetry panels stagger
40ms apart, audit rows cascade last. Live values tick with a 120ms numeric
transition. Kill-switch engage triggers a single 400ms border pulse on the frame —
the only attention-grabbing animation in the app.

## Components

- **StatusPill** — dot + uppercase mono label, colored by state token.
- **MetricPanel** — label, large mono value, unit suffix, optional limit bar.
- **LimitBar** — 4px track, fill colored `--live`/`--armed`/`--breach` by utilization.
- **KillSwitch** — two-stage: arm, then confirm. Destructive styling only when armed.
- **AuditRow** — timestamp (mono dim), decision verdict pill, subject, reason.
- **ConnectionBanner** — shows the configured governor endpoint and whether it is
  reachable; explains fallback to local state when it is not.

## UX patterns

- Status before detail: the top rail answers "is it safe, is it live, is it halted" in one glance.
- Every mutating control is two-stage and writes an audit entry.
- Unreachable governor degrades gracefully to seeded local state, clearly labeled `LOCAL` — never silently pretends to be live.
