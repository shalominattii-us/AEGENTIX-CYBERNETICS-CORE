import { seal } from "./headers.js";

export class HttpError extends Error {
  constructor(
    readonly status: number,
    readonly body: Record<string, unknown>,
    readonly headers?: Record<string, string>,
  ) {
    super(typeof body.error === "string" ? body.error : "request failed");
  }
}

export function json(request: Request, status: number, body: unknown, extra?: Record<string, string>): Response {
  return seal(
    request,
    new Response(JSON.stringify(body), {
      status,
      headers: {
        "content-type": "application/json; charset=utf-8",
        "cache-control": "no-store",
        ...extra,
      },
    }),
  );
}

export function clientKey(request: Request): string {
  // Cloudflare sets CF-Connecting-IP. Do not trust X-Forwarded-For from clients.
  // Missing header shares the "unknown" bucket, which is stricter than inventing keys.
  const value = request.headers.get("CF-Connecting-IP") ?? "";
  if (/^[0-9A-Fa-f:.]{3,64}$/.test(value)) return `ip:${value}`;
  return "ip:unknown";
}
