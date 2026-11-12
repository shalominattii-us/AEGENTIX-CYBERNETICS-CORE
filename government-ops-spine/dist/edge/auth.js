import { timingSafeEqual } from 'node:crypto';
const encoder = new TextEncoder();
export async function ingestAuthorized(request, token) {
    const expected = token?.trim() ?? '';
    if (!expected)
        return false;
    const header = request.headers.get('authorization') ?? '';
    const provided = /^bearer\s+/i.test(header) ? header.replace(/^bearer\s+/i, '').trim() : '';
    if (!provided)
        return false;
    const [providedHash, expectedHash] = await Promise.all([
        crypto.subtle.digest('SHA-256', encoder.encode(provided)),
        crypto.subtle.digest('SHA-256', encoder.encode(expected))
    ]);
    return timingSafeEqual(new Uint8Array(providedHash), new Uint8Array(expectedHash));
}
