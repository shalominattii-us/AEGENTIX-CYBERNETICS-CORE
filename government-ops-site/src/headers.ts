const CSP_BASE = [
  "default-src 'self'",
  "script-src 'self'",
  "style-src 'self'",
  "img-src 'self'",
  "font-src 'self'",
  "connect-src 'self'",
  "object-src 'none'",
  "base-uri 'none'",
  "frame-ancestors 'none'",
  "form-action 'none'",
  "frame-src 'none'",
  "worker-src 'none'",
].join("; ");

export function securityHeaders(request: Request): Headers {
  const headers = new Headers();
  const https = new URL(request.url).protocol === "https:";
  headers.set("content-security-policy", https ? `${CSP_BASE}; upgrade-insecure-requests` : CSP_BASE);
  headers.set("x-content-type-options", "nosniff");
  headers.set("referrer-policy", "no-referrer");
  headers.set("x-frame-options", "DENY");
  headers.set("cross-origin-opener-policy", "same-origin");
  headers.set("cross-origin-resource-policy", "same-origin");
  headers.set(
    "permissions-policy",
    "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
  );
  headers.set("x-site-mode", "public-read-only");
  if (https) {
    headers.set("strict-transport-security", "max-age=31536000; includeSubDomains; preload");
  }
  return headers;
}

export function seal(request: Request, response: Response, extra?: HeadersInit): Response {
  const headers = new Headers(response.headers);
  securityHeaders(request).forEach((value, key) => headers.set(key, value));
  if (extra) new Headers(extra).forEach((value, key) => headers.set(key, value));
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}
