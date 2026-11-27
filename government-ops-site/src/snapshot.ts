export interface PublicSnapshotRecord {
  id: string;
  title: string;
  issuer: string;
  jurisdiction: string;
  opportunityType: string;
  status: "sample-open" | "sample-closed" | "sample-cancelled";
  publicationDate: string;
  deadline: string | null;
  summary: string;
  setAside: null;
  provenance: { system: "sample-snapshot"; note: string };
}

export interface PublicSnapshot {
  kind: "sanitized-public-snapshot";
  fictional: true;
  snapshotId: string;
  publishedAt: string;
  label: "SAMPLE DATA";
  disclaimer: string;
  source: "static-file";
  readOnly: true;
  records: PublicSnapshotRecord[];
}

const FORBIDDEN_KEYS = new Set([
  "uei",
  "ueisam",
  "cage",
  "cagecode",
  "email",
  "emails",
  "phone",
  "ssn",
  "tin",
  "ein",
  "apikey",
  "token",
  "password",
  "secret",
  "authorization",
  "authorizationtoken",
  "pointofcontact",
  "contactname",
  "firstname",
  "lastname",
]);

const EMAIL = /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i;
const IDENTIFIER_ASSIGNMENT = /\b(UEI|CAGE|DUNS)\s*[:=#]\s*\S+/i;
const STATUSES = new Set(["sample-open", "sample-closed", "sample-cancelled"]);

export function validateSnapshot(value: unknown): PublicSnapshot {
  if (!value || typeof value !== "object") throw new Error("Snapshot must be an object.");
  walk(value, "$");
  const record = value as Record<string, unknown>;
  if (record.kind !== "sanitized-public-snapshot") throw new Error("Snapshot kind is not public.");
  if (record.fictional !== true) throw new Error("Snapshot must be marked fictional.");
  if (record.label !== "SAMPLE DATA") throw new Error("Snapshot label is missing.");
  if (record.source !== "static-file") throw new Error("Snapshot source must be the static file.");
  if (record.readOnly !== true) throw new Error("Snapshot must be read-only.");
  if (typeof record.snapshotId !== "string" || typeof record.publishedAt !== "string" || typeof record.disclaimer !== "string") {
    throw new Error("Snapshot metadata is incomplete.");
  }
  if (!Array.isArray(record.records) || record.records.length < 1 || record.records.length > 50) {
    throw new Error("Snapshot records are missing.");
  }
  const seen = new Set<string>();
  const records = record.records.map((item) => validateRecord(item, seen));
  return {
    kind: "sanitized-public-snapshot",
    fictional: true,
    snapshotId: record.snapshotId,
    publishedAt: record.publishedAt,
    label: "SAMPLE DATA",
    disclaimer: record.disclaimer,
    source: "static-file",
    readOnly: true,
    records,
  };
}

function validateRecord(value: unknown, seen: Set<string>): PublicSnapshotRecord {
  if (!value || typeof value !== "object") throw new Error("Snapshot record is invalid.");
  const record = value as Record<string, unknown>;
  const id = stringField(record, "id");
  if (!/^SAMPLE-[A-Z0-9-]{2,40}$/.test(id)) throw new Error("Snapshot record id is invalid.");
  if (seen.has(id)) throw new Error("Snapshot record id is duplicated.");
  seen.add(id);
  const issuer = stringField(record, "issuer");
  if (!/fictional/i.test(issuer)) throw new Error("Snapshot issuer must be marked fictional.");
  const status = stringField(record, "status");
  if (!STATUSES.has(status)) throw new Error("Snapshot status is invalid.");
  if (record.setAside !== null) throw new Error("Snapshot set-aside must be null.");
  const provenance = record.provenance;
  if (!provenance || typeof provenance !== "object") throw new Error("Snapshot provenance is missing.");
  const source = provenance as Record<string, unknown>;
  if (source.system !== "sample-snapshot") throw new Error("Snapshot provenance system is invalid.");
  if (typeof source.note !== "string" || source.note.length < 12) throw new Error("Snapshot provenance note is missing.");
  const deadline = record.deadline;
  if (deadline !== null && typeof deadline !== "string") throw new Error("Snapshot deadline is invalid.");
  return {
    id,
    title: stringField(record, "title"),
    issuer,
    jurisdiction: stringField(record, "jurisdiction"),
    opportunityType: stringField(record, "opportunityType"),
    status: status as PublicSnapshotRecord["status"],
    publicationDate: stringField(record, "publicationDate"),
    deadline,
    summary: stringField(record, "summary"),
    setAside: null,
    provenance: { system: "sample-snapshot", note: source.note },
  };
}

function stringField(record: Record<string, unknown>, key: string): string {
  const value = record[key];
  if (typeof value !== "string" || !value.trim() || value.length > 2000) throw new Error(`Snapshot field ${key} is invalid.`);
  return value.trim();
}

function walk(value: unknown, path: string): void {
  if (Array.isArray(value)) {
    value.forEach((item, index) => walk(item, `${path}[${index}]`));
    return;
  }
  if (value && typeof value === "object") {
    for (const [key, child] of Object.entries(value)) {
      const normalized = key.toLowerCase().replace(/[_-]/g, "");
      if (FORBIDDEN_KEYS.has(normalized)) throw new Error(`Forbidden snapshot field at ${path}.${key}`);
      walk(child, `${path}.${key}`);
    }
    return;
  }
  if (typeof value === "string") {
    if (EMAIL.test(value)) throw new Error(`Email-like snapshot value at ${path}`);
    if (IDENTIFIER_ASSIGNMENT.test(value)) throw new Error(`Identifier-like snapshot value at ${path}`);
  }
}

export async function readSnapshot(fetchAsset: (request: Request) => Promise<Response>, requestUrl: string): Promise<PublicSnapshot> {
  const assetUrl = new URL("/snapshot/opportunities.json", requestUrl);
  const response = await fetchAsset(new Request(assetUrl, { method: "GET" }));
  if (!response.ok) throw new Error("Sample snapshot file is unavailable.");
  let parsed: unknown;
  try {
    parsed = await response.json();
  } catch {
    throw new Error("Sample snapshot file is not JSON.");
  }
  return validateSnapshot(parsed);
}
