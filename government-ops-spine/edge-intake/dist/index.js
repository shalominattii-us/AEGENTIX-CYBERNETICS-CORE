var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// ../src/foundry-bridge.ts
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

// ../src/sam-gov.ts
var DEFAULT_ENDPOINT = "https://api.sam.gov/opportunities/v2/search";
var DEFAULT_TIMEOUT_MS = 3e4;
function redactSecrets(text2, secrets) {
  let redacted = text2;
  const patterns = [/([?&#]api_key=)[^&\s#]+/gi, /(api_key(?:=|%3D|":\s*"))[^&\s"',}]+/gi];
  for (const secret of secrets) {
    const trimmed = secret.trim();
    if (trimmed.length < 8) continue;
    redacted = redacted.split(trimmed).join("[redacted]");
  }
  for (const pattern of patterns) redacted = redacted.replace(pattern, "$1[redacted]");
  return redacted;
}
__name(redactSecrets, "redactSecrets");
function assertOfficialSamEndpoint(endpoint) {
  let url;
  try {
    url = new URL(endpoint);
  } catch {
    throw new Error("SAM.gov endpoint must be an https URL on api.sam.gov");
  }
  if (url.protocol !== "https:" || url.hostname !== "api.sam.gov") {
    throw new Error("SAM.gov endpoint host must be api.sam.gov");
  }
  return url;
}
__name(assertOfficialSamEndpoint, "assertOfficialSamEndpoint");
function formatSamDate(date) {
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  return `${month}/${day}/${date.getUTCFullYear()}`;
}
__name(formatSamDate, "formatSamDate");
function assertSamDate(value, label) {
  if (!/^(0[1-9]|1[0-2])\/(0[1-9]|[12]\d|3[01])\/\d{4}$/.test(value)) {
    throw new Error(`${label} must use MM/dd/yyyy`);
  }
  return value;
}
__name(assertSamDate, "assertSamDate");
async function searchSamGov(request) {
  const apiKey = request.apiKey.trim();
  if (!apiKey) throw new Error("SAM_GOV_API_KEY is required");
  const postedFrom = assertSamDate(request.postedFrom, "postedFrom");
  const postedTo = assertSamDate(request.postedTo, "postedTo");
  const limit = clamp(request.limit ?? 100, 1, 1e3);
  const maxPages = clamp(request.maxPages ?? 5, 1, 50);
  const fetchImpl = request.fetchImpl ?? fetch;
  const endpoint = request.endpoint ?? DEFAULT_ENDPOINT;
  assertOfficialSamEndpoint(endpoint);
  const notices = [];
  let offset = request.offset ?? 0;
  if (offset < 0) throw new Error("offset cannot be negative");
  for (let page = 0; page < maxPages; page += 1) {
    const payload = await fetchSamPage({
      apiKey,
      endpoint,
      postedFrom,
      postedTo,
      limit,
      offset,
      naics: request.naics,
      title: request.title,
      noticeType: request.noticeType,
      organization: request.organization,
      timeoutMs: request.timeoutMs ?? DEFAULT_TIMEOUT_MS,
      fetchImpl
    });
    const batch = payload.opportunitiesData ?? [];
    notices.push(...batch);
    const total = typeof payload.totalRecords === "number" ? payload.totalRecords : offset + batch.length;
    offset += batch.length;
    if (batch.length === 0 || batch.length < limit || offset >= total) break;
  }
  return notices;
}
__name(searchSamGov, "searchSamGov");
async function fetchSamPage(input) {
  const url = new URL(input.endpoint);
  url.searchParams.set("api_key", input.apiKey);
  url.searchParams.set("postedFrom", input.postedFrom);
  url.searchParams.set("postedTo", input.postedTo);
  url.searchParams.set("limit", String(input.limit));
  url.searchParams.set("offset", String(input.offset));
  if (input.naics) url.searchParams.set("ncode", input.naics);
  if (input.title) url.searchParams.set("title", input.title);
  if (input.noticeType) url.searchParams.set("ptype", input.noticeType);
  if (input.organization) url.searchParams.set("organizationName", input.organization);
  let response;
  try {
    response = await input.fetchImpl(url, {
      method: "GET",
      redirect: "manual",
      headers: {
        accept: "application/json",
        "user-agent": "government-ops-spine-sam-gov/1.0"
      },
      signal: AbortSignal.timeout(input.timeoutMs)
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    throw new Error(`SAM.gov request failed: ${redactSecrets(message, [input.apiKey])}`);
  }
  if (response.status >= 300 && response.status < 400) {
    throw new Error(`SAM.gov redirect was not followed (${response.status})`);
  }
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`SAM.gov returned HTTP ${response.status}: ${redactSecrets(body.slice(0, 500), [input.apiKey])}`);
  }
  let parsed;
  try {
    parsed = JSON.parse(body);
  } catch {
    throw new Error("SAM.gov response was not valid JSON");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw new Error("SAM.gov response must be a JSON object");
  }
  const record = parsed;
  const opportunities = record.opportunitiesData ?? [];
  if (!Array.isArray(opportunities)) throw new Error("SAM.gov response opportunitiesData must be a list");
  return {
    totalRecords: typeof record.totalRecords === "number" ? record.totalRecords : void 0,
    opportunitiesData: opportunities.filter((item) => Boolean(item) && typeof item === "object" && !Array.isArray(item))
  };
}
__name(fetchSamPage, "fetchSamPage");
function clamp(value, min, max) {
  if (!Number.isFinite(value)) return min;
  return Math.min(max, Math.max(min, Math.trunc(value)));
}
__name(clamp, "clamp");

// ../src/foundry-bridge.ts
var DEFAULT_FOUNDRY_DISPOSITIONS = ["HUMAN_REVIEW"];
var DEFAULT_FOUNDRY_NAICS = ["541512", "541715"];
function parseFilterList(value, fallback) {
  if (value === void 0) return [...fallback];
  const trimmed = value.trim();
  if (!trimmed || trimmed === "*" || trimmed.toLowerCase() === "any") return [];
  return [...new Set(trimmed.split(/[\s,]+/).map((part) => part.trim()).filter(Boolean))];
}
__name(parseFilterList, "parseFilterList");
function parseDispositionList(value, fallback = DEFAULT_FOUNDRY_DISPOSITIONS) {
  return parseFilterList(value, fallback).map((item) => item.toUpperCase());
}
__name(parseDispositionList, "parseDispositionList");
function parseNaicsList(value, fallback = DEFAULT_FOUNDRY_NAICS) {
  const raw = parseFilterList(value, fallback);
  if (!raw.length) return [];
  return [...new Set(raw.flatMap((token) => extractNaicsCodes(token)))].sort();
}
__name(parseNaicsList, "parseNaicsList");
function opportunityFromFoundry(input, options) {
  const intelligence = extractIntelligence(input);
  const intermediate = intermediateFromUnknown(input);
  if (!intermediate.retrievedAt && options.retrievedAt) intermediate.retrievedAt = options.retrievedAt;
  const opportunity = toPublicOpportunity(intermediate, options.retrievedAt ?? (/* @__PURE__ */ new Date(0)).toISOString());
  return {
    origin: options.origin,
    externalId: opportunity.externalId,
    title: opportunity.title,
    naics: intermediate.naics,
    intelligence: intelligence ?? extractIntelligence(isRecord(input) ? input.metadata : void 0),
    opportunity
  };
}
__name(opportunityFromFoundry, "opportunityFromFoundry");
function selectFoundryRecords(records, options) {
  const skipped = [];
  const seen = /* @__PURE__ */ new Map();
  for (const record of records) {
    const disposition = dispositionDecision(record, options.dispositions);
    if (!disposition.ok) {
      skipped.push({ externalId: record.externalId, title: record.title, reason: disposition.reason });
      continue;
    }
    const naics = naicsDecision(record.naics, options.naics);
    if (!naics.ok) {
      skipped.push({ externalId: record.externalId, title: record.title, reason: naics.reason });
      continue;
    }
    const identity = `${record.opportunity.provenance[0]?.system ?? "unknown"}:${record.externalId}`;
    const previous = seen.get(identity);
    if (previous) skipped.push({ externalId: previous.externalId, title: previous.title, reason: "duplicate" });
    seen.set(identity, record);
  }
  const selected = [...seen.values()].sort((a, b) => a.externalId.localeCompare(b.externalId));
  return { selected, skipped };
}
__name(selectFoundryRecords, "selectFoundryRecords");
function recordsFromFoundryDocument(json2, options = {}) {
  const sourceRunId = options.sourceRunId ?? "foundry-document";
  if (isRecord(json2) && Array.isArray(json2.opportunitiesData)) {
    return recordsBatch(sourceRunId, "foundry-report", json2.opportunitiesData, options.receivedAt ?? receivedAtFrom(json2));
  }
  if (Array.isArray(json2)) return recordsBatch(sourceRunId, "foundry-report", json2, options.receivedAt);
  if (isRecord(json2) && Array.isArray(json2.opportunities) && !json2.opportunity_id) {
    return recordsBatch(sourceRunId, "foundry-report", json2.opportunities, options.receivedAt ?? receivedAtFrom(json2));
  }
  if (isRecord(json2) && Array.isArray(json2.records)) {
    return recordsBatch(sourceRunId, "foundry-report", json2.records, options.receivedAt ?? receivedAtFrom(json2));
  }
  return recordsBatch(sourceRunId, "foundry-report", [json2], options.receivedAt);
}
__name(recordsFromFoundryDocument, "recordsFromFoundryDocument");
function recordsBatch(sourceRunId, origin, items, receivedAt) {
  const records = [];
  const errors = [];
  items.forEach((item, index) => {
    try {
      records.push(opportunityFromFoundry(item, { origin, retrievedAt: receivedAt }));
    } catch (error) {
      errors.push({ message: `record ${index + 1}: ${error instanceof Error ? error.message : String(error)}` });
    }
  });
  return { sourceRunId, receivedAt, records, errors };
}
__name(recordsBatch, "recordsBatch");
function toPublicOpportunity(input, retrievedAtFallback) {
  const sourceName = input.sourceName.trim();
  const official = isSamGovSource(sourceName);
  const system = official ? "SAM.gov" : sourceName || "unknown";
  const externalId = input.externalId.trim();
  const title = collapse(input.title);
  if (!externalId) throw new Error(title ? `Missing notice id for "${title}"` : "Missing notice id");
  if (!title) throw new Error(externalId ? `Missing title for ${externalId}` : "Missing title");
  const url = input.sourceUrl?.trim() || (official ? `https://sam.gov/opp/${encodeURIComponent(externalId)}/view` : "");
  if (!url) throw new Error(`Missing source URL for ${externalId}`);
  const issuer = collapse(input.issuer || "") || (official ? "Unknown agency" : "Unknown issuer");
  const jurisdiction = collapse(input.jurisdiction || "") || (official ? "United States" : "Unknown");
  const description = proseDescription(input.description);
  const typeText = input.typeText || "";
  let summary = description || composeSummary({ title, typeText, issuer, externalId, naics: input.naics, setAside: input.setAside });
  if (/award notice/i.test(typeText) && !/award notice/i.test(`${title} ${summary}`)) summary = `Award Notice. ${summary}`;
  if (/cancell?ed/i.test(`${input.statusText ?? ""} ${typeText}`) && !/cancell?ed/i.test(`${title} ${summary}`)) summary = `Cancelled. ${summary}`;
  const provenance = {
    system,
    authority: official ? "official" : "aggregator",
    url,
    retrievedAt: input.retrievedAt || retrievedAtFallback,
    ...input.contentHash ? { contentHash: input.contentHash } : {},
    ...input.attachments.length ? { attachmentUrls: [...input.attachments].sort() } : {}
  };
  const registrations = new Set(input.registrations);
  if (official) registrations.add("SAM.gov");
  const amount2 = input.amountMax ?? input.amountMin;
  const opportunity = {
    schemaVersion: "1.0.0",
    eventId: `${sourcePrefix(system)}:${externalId}`,
    externalId,
    title,
    issuer,
    jurisdiction,
    opportunityType: classifyOpportunityType(typeText, title),
    ...input.publishedDate ? { publicationDate: input.publishedDate } : {},
    ...input.updateDate ? { updateDate: input.updateDate } : {},
    ...input.deadline ? { deadline: input.deadline } : {},
    ...amount2 !== void 0 ? { value: { amount: amount2, currency: input.currency || "USD", ...rangeText(input) ? { text: rangeText(input) } : {} } } : {},
    eligibility: input.eligibility,
    ...input.setAside ? { setAside: input.setAside } : {},
    ...input.location ? { location: input.location } : {},
    submissionMethod: official ? "SAM.gov" : void 0,
    requiredRegistrations: [...registrations],
    summary,
    rawText: buildRawText(input, description),
    provenance: [provenance]
  };
  if (!opportunity.submissionMethod) delete opportunity.submissionMethod;
  return opportunity;
}
__name(toPublicOpportunity, "toPublicOpportunity");
function intermediateFromUnknown(input) {
  const record = unwrapOpportunity(input);
  if (isRawSamNotice(record)) return intermediateFromRawSam(record);
  return intermediateFromCanonicalOrNormalized(record);
}
__name(intermediateFromUnknown, "intermediateFromUnknown");
function unwrapOpportunity(input) {
  if (!isRecord(input)) throw new Error("Opportunity JSON must be an object");
  if (isRecord(input.opportunity)) return input.opportunity;
  return input;
}
__name(unwrapOpportunity, "unwrapOpportunity");
function intermediateFromCanonicalOrNormalized(record) {
  const metadata = isRecord(record.metadata) ? record.metadata : record;
  const samRaw = isRecord(metadata.sam_raw) ? metadata.sam_raw : isRawSamNotice(metadata) ? metadata : {};
  const provenance = isRecord(record.provenance) ? record.provenance : {};
  const externalId = text(record.external_id) || text(provenance.source_record_id) || text(metadata.external_id) || text(metadata.record_id) || text(samRaw.noticeId) || text(record.noticeId);
  const sourceName = text(record.source) || text(provenance.source_name) || text(metadata.source) || "unknown";
  const sourceUrl = text(samRaw.uiLink) || text(metadata.source_url) || text(provenance.source_url) || text(record.source_url) || text(metadata.submission_path);
  const deadline = firstDate(samRaw.responseDeadLine, metadata.deadline, record.deadline);
  const published = firstDate(record.published_date, metadata.published_date, samRaw.postedDate);
  const updated = firstDate(metadata.update_date, samRaw.modifiedDate, record.update_date);
  const naics = uniqueNaics(record.sectors, metadata.naics, metadata.sectors, metadata.naicsCode, samRaw.naicsCode, samRaw.naicsCodes);
  const contacts = contactsFrom(metadata.contact ?? metadata.pointOfContact ?? samRaw.pointOfContact);
  const attachments = uniqueStrings(record.attachments, metadata.attachments, samRaw.resourceLinks);
  return {
    externalId: externalId ?? "",
    title: text(record.title) || text(metadata.title) || "",
    sourceName,
    sourceUrl,
    issuer: text(record.issuer) || text(metadata.issuer) || text(metadata.agency) || text(samRaw.fullParentPathName) || text(samRaw.department),
    jurisdiction: text(record.jurisdiction) || text(metadata.jurisdiction),
    typeText: [text(record.opportunity_type), text(record.type), text(metadata.type), text(metadata.opportunity_type), text(samRaw.type), text(samRaw.baseType)].filter(Boolean).join(" "),
    statusText: text(record.status) || text(metadata.status) || text(samRaw.active),
    publishedDate: published,
    updateDate: updated,
    deadline,
    naics,
    psc: text(metadata.psc) || text(samRaw.classificationCode),
    setAside: text(metadata.set_aside) || text(samRaw.typeOfSetAsideDescription) || text(samRaw.typeOfSetAside),
    description: text(metadata.description) || text(samRaw.description) || text(record.description),
    attachments,
    location: formatLocation(metadata.location ?? samRaw.placeOfPerformance),
    contacts,
    solicitationNumber: text(metadata.solicitation_number) || text(samRaw.solicitationNumber),
    office: text(metadata.office) || text(samRaw.office),
    eligibility: stringList(record.eligibility ?? metadata.eligibility),
    registrations: stringList(metadata.registration_requirements),
    amountMin: amount(record.amount_min ?? metadata.amount_min),
    amountMax: amount(record.amount_max ?? metadata.amount_max ?? awardAmount(samRaw.award)),
    currency: text(record.currency) || text(metadata.currency) || void 0,
    retrievedAt: text(provenance.retrieved_at) || text(metadata.retrieved_at) || text(metadata.source_checked_at),
    contentHash: text(provenance.content_hash) || text(metadata.content_hash),
    activeText: text(samRaw.active) || text(metadata.active)
  };
}
__name(intermediateFromCanonicalOrNormalized, "intermediateFromCanonicalOrNormalized");
function intermediateFromRawSam(record) {
  const noticeId = text(record.noticeId) ?? "";
  const uiLink = text(record.uiLink) || (noticeId ? `https://sam.gov/opp/${encodeURIComponent(noticeId)}/view` : void 0);
  return intermediateFromCanonicalOrNormalized({
    external_id: noticeId,
    title: text(record.title),
    source: "SAM.gov",
    source_url: uiLink,
    issuer: text(record.fullParentPathName) || text(record.department),
    jurisdiction: "United States",
    type: text(record.type) || text(record.baseType),
    status: activeStatus(record.active),
    published_date: text(record.postedDate),
    deadline: text(record.responseDeadLine),
    naics: naicsList(record.naicsCode, record.naicsCodes),
    psc: text(record.classificationCode),
    set_aside: text(record.typeOfSetAsideDescription) || text(record.typeOfSetAside),
    description: text(record.description),
    attachments: stringList(record.resourceLinks),
    solicitation_number: text(record.solicitationNumber),
    office: text(record.office),
    location: record.placeOfPerformance,
    contact: record.pointOfContact,
    amount_max: awardAmount(record.award),
    sam_raw: record
  });
}
__name(intermediateFromRawSam, "intermediateFromRawSam");
function dispositionDecision(record, allow) {
  if (!allow.length || record.origin === "sam-api" || record.origin === "sam-public") return { ok: true };
  if (!record.intelligence) return { ok: false, reason: "disposition_missing" };
  const stage = record.intelligence.stage.toUpperCase();
  const disposition = record.intelligence.disposition.toUpperCase();
  const ok = allow.some((item) => item.toUpperCase() === stage || item.toUpperCase() === disposition);
  return ok ? { ok: true } : { ok: false, reason: "disposition" };
}
__name(dispositionDecision, "dispositionDecision");
function naicsDecision(codes, allow) {
  if (!allow.length) return { ok: true };
  if (!codes.length) return { ok: false, reason: "naics_missing" };
  return codes.some((code) => allow.includes(code)) ? { ok: true } : { ok: false, reason: "naics" };
}
__name(naicsDecision, "naicsDecision");
function extractIntelligence(input) {
  if (!isRecord(input)) return void 0;
  for (const candidate of [input.intelligence_output, input.intelligence, input]) {
    if (!isRecord(candidate) || !isRecord(candidate.maturity)) continue;
    const stage = text(candidate.maturity.stage);
    const disposition = text(candidate.maturity.disposition);
    if (!stage && !disposition) continue;
    return { stage: stage || disposition || "", disposition: disposition || stage || "" };
  }
  return void 0;
}
__name(extractIntelligence, "extractIntelligence");
function classifyOpportunityType(typeText, title) {
  const blob = `${typeText} ${title}`;
  const rules = [
    [/\bSTTR\b/i, "STTR"],
    [/\bSBIR\b/i, "SBIR"],
    [/\bBAA\b|broad agency announcement/i, "BAA"],
    [/\bCSO\b|commercial solutions opening/i, "CSO"],
    [/\bOTA\b|other transaction/i, "OTA"],
    [/\bIFB\b|invitation for bids?/i, "IFB"],
    [/\bRFQ\b|request for quotations?/i, "RFQ"],
    [/\bRFI\b|request for information/i, "RFI"],
    [/sources sought/i, "SOURCES_SOUGHT"],
    [/cooperative agreement/i, "COOPERATIVE_AGREEMENT"],
    [/\bgrants?\b/i, "GRANT"],
    [/\bprizes?\b/i, "PRIZE"],
    [/\bchallenges?\b/i, "CHALLENGE"],
    [/forecast|presolicitation/i, "FORECAST"],
    [/licen[cs]ing/i, "LICENSING"],
    [/partnership/i, "PARTNERSHIP"],
    [/subcontract/i, "SUBCONTRACT"],
    [/solicitation|combined synopsis|\bRFP\b|request for proposals?/i, "RFP"]
  ];
  for (const [pattern, type] of rules) if (pattern.test(blob)) return type;
  return "OTHER";
}
__name(classifyOpportunityType, "classifyOpportunityType");
function buildRawText(input, description) {
  const lines = [
    `Title: ${collapse(input.title)}`,
    `Notice ID: ${input.externalId}`,
    input.solicitationNumber ? `Solicitation: ${input.solicitationNumber}` : void 0,
    input.typeText ? `Type: ${collapse(input.typeText)}` : void 0,
    input.issuer ? `Agency: ${collapse(input.issuer)}` : void 0,
    input.office ? `Office: ${input.office}` : void 0,
    input.naics.length ? `NAICS: ${input.naics.join(", ")}` : void 0,
    input.psc ? `PSC: ${input.psc}` : void 0,
    input.setAside ? `Set-aside: ${input.setAside}` : void 0,
    input.statusText ? `Status: ${input.statusText}` : void 0,
    input.activeText ? `Active: ${input.activeText}` : void 0,
    input.location ? `Location: ${input.location}` : void 0,
    description ? `Description: ${description}` : input.description ? `Description URL: ${input.description}` : void 0,
    ...input.contacts.map((contact) => `Contact: ${[contact.name, contact.type, contact.email, contact.phone].filter(Boolean).join(" | ")}`)
  ];
  return lines.filter((line) => Boolean(line)).join("\n");
}
__name(buildRawText, "buildRawText");
function composeSummary(input) {
  const typeLabel = collapse(input.typeText) || "opportunity";
  const naics = input.naics.length ? ` NAICS ${input.naics.join(", ")}.` : "";
  const setAside = input.setAside ? ` Set-aside: ${input.setAside}.` : "";
  return `${input.title}. ${typeLabel} issued by ${input.issuer}. Notice ${input.externalId}.${naics}${setAside}`;
}
__name(composeSummary, "composeSummary");
function proseDescription(value) {
  if (!value) return void 0;
  const trimmed = collapse(value);
  if (/^https?:\/\//i.test(trimmed)) return void 0;
  return trimmed;
}
__name(proseDescription, "proseDescription");
function formatLocation(value) {
  if (typeof value === "string") return collapse(value) || void 0;
  if (!isRecord(value)) return void 0;
  const city = nestedText(value.city, "name") || text(value.city);
  const state = nestedText(value.state, "code") || text(value.state);
  const postal = text(value.postal_code) || text(value.zip) || text(value.postalCode);
  const country = nestedText(value.country, "code") || text(value.country);
  const parts = [city, state, postal, country].map((part) => part?.trim()).filter(Boolean);
  return parts.length ? parts.join(", ") : void 0;
}
__name(formatLocation, "formatLocation");
function contactsFrom(value) {
  const items = Array.isArray(value) ? value : value ? [value] : [];
  const contacts = items.filter(isRecord).map((item) => ({
    name: text(item.fullname) || text(item.fullName) || text(item.name),
    email: text(item.email),
    phone: text(item.phone),
    type: text(item.type)
  })).filter((contact) => contact.name || contact.email || contact.phone);
  contacts.sort((a, b) => `${a.type ?? ""}:${a.name ?? ""}:${a.email ?? ""}`.localeCompare(`${b.type ?? ""}:${b.name ?? ""}:${b.email ?? ""}`));
  return contacts;
}
__name(contactsFrom, "contactsFrom");
function firstDate(...values) {
  for (const value of values) {
    const parsed = dateText(value);
    if (parsed) return parsed;
  }
  return void 0;
}
__name(firstDate, "firstDate");
function dateText(value) {
  const raw = text(value);
  if (!raw) return void 0;
  const stamp = Date.parse(raw);
  if (Number.isNaN(stamp)) return void 0;
  return raw;
}
__name(dateText, "dateText");
function amount(value) {
  if (typeof value === "number" && Number.isFinite(value) && value >= 0) return value;
  if (typeof value !== "string") return void 0;
  const cleaned = value.replace(/[$,\s]/g, "");
  if (!cleaned) return void 0;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : void 0;
}
__name(amount, "amount");
function awardAmount(value) {
  if (!isRecord(value)) return void 0;
  return amount(value.amount);
}
__name(awardAmount, "awardAmount");
function rangeText(input) {
  if (input.amountMin === void 0 || input.amountMax === void 0 || input.amountMin === input.amountMax) return void 0;
  return `${input.amountMin}-${input.amountMax} ${input.currency || "USD"}`;
}
__name(rangeText, "rangeText");
function activeStatus(value) {
  if (typeof value === "boolean") return value ? "open" : "inactive";
  const raw = text(value);
  if (!raw) return "open";
  if (/^(no|false|inactive|n)$/i.test(raw)) return "inactive";
  return "open";
}
__name(activeStatus, "activeStatus");
function isSamGovSource(sourceName) {
  const normalized = sourceName.toLowerCase().replace(/[\s._-]+/g, "");
  return normalized === "samgov" || normalized === "apisamgov";
}
__name(isSamGovSource, "isSamGovSource");
function sourcePrefix(system) {
  if (system === "SAM.gov") return "sam";
  const slug = system.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  return slug || "source";
}
__name(sourcePrefix, "sourcePrefix");
function extractNaicsCodes(value) {
  const found = /* @__PURE__ */ new Set();
  collectNaics(value, found);
  return [...found].sort();
}
__name(extractNaicsCodes, "extractNaicsCodes");
function uniqueNaics(...values) {
  return [...new Set(values.flatMap((value) => extractNaicsCodes(value)))].sort();
}
__name(uniqueNaics, "uniqueNaics");
function collectNaics(value, into) {
  if (typeof value === "number" && Number.isFinite(value)) {
    addNaics(String(Math.trunc(value)), into);
    return;
  }
  if (typeof value === "string") {
    addNaics(value, into);
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) collectNaics(item, into);
    return;
  }
  if (isRecord(value)) {
    if ("code" in value) collectNaics(value.code, into);
    if ("naicsCode" in value) collectNaics(value.naicsCode, into);
  }
}
__name(collectNaics, "collectNaics");
function addNaics(value, into) {
  const trimmed = value.trim();
  if (/^\d{6}$/.test(trimmed)) {
    into.add(trimmed);
    return;
  }
  for (const match of trimmed.matchAll(/\b\d{6}\b/g)) into.add(match[0]);
}
__name(addNaics, "addNaics");
function naicsList(...values) {
  return uniqueNaics(...values);
}
__name(naicsList, "naicsList");
function stringList(...values) {
  const found = [];
  for (const value of values) {
    if (typeof value === "string" && value.trim()) found.push(value.trim());
    else if (Array.isArray(value)) {
      for (const item of value) if (typeof item === "string" && item.trim()) found.push(item.trim());
    }
  }
  return [...new Set(found)].sort();
}
__name(stringList, "stringList");
function uniqueStrings(...values) {
  return stringList(...values);
}
__name(uniqueStrings, "uniqueStrings");
function nestedText(value, key) {
  if (isRecord(value)) return text(value[key]);
  return text(value);
}
__name(nestedText, "nestedText");
function text(value) {
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed || void 0;
  }
  if (typeof value === "number" && Number.isFinite(value)) return String(value);
  return void 0;
}
__name(text, "text");
function collapse(value) {
  return value.trim().replace(/\s+/g, " ");
}
__name(collapse, "collapse");
function receivedAtFrom(record) {
  return text(record.generated_at) || text(record.retrieved_at);
}
__name(receivedAtFrom, "receivedAtFrom");
function isRawSamNotice(value) {
  return isRecord(value) && typeof value.noticeId === "string" && value.opportunity_id == null && value.external_id == null && !isRecord(value.opportunity);
}
__name(isRawSamNotice, "isRawSamNotice");
function isRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
__name(isRecord, "isRecord");

// ../src/edge/auth.ts
import { timingSafeEqual } from "node:crypto";
var encoder = new TextEncoder();
async function ingestAuthorized(request, token) {
  const expected = token?.trim() ?? "";
  if (!expected) return false;
  const header = request.headers.get("authorization") ?? "";
  const provided = /^bearer\s+/i.test(header) ? header.replace(/^bearer\s+/i, "").trim() : "";
  if (!provided) return false;
  const [providedHash, expectedHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(provided)),
    crypto.subtle.digest("SHA-256", encoder.encode(expected))
  ]);
  return timingSafeEqual(new Uint8Array(providedHash), new Uint8Array(expectedHash));
}
__name(ingestAuthorized, "ingestAuthorized");

// ../src/edge/public-extract.ts
var SAM_PUBLIC_OPPORTUNITIES_CSV = "https://sam.gov/api/prod/fileextractservices/v1/api/download/Contract%20Opportunities/datagov/ContractOpportunitiesFullCSV.csv?privacy=Public";
async function pullSamPublicExtract(options) {
  const parser = createContractOpportunityParser(options);
  if (options.csvText !== void 0) {
    parser.push(options.csvText);
    parser.finish();
    return parser.stats();
  }
  const fetchImpl = options.fetchImpl ?? fetch;
  const response = await fetchImpl(options.url ?? SAM_PUBLIC_OPPORTUNITIES_CSV, {
    redirect: "follow",
    headers: { accept: "text/csv,*/*", "user-agent": "gov-opportunity-intake/1.0" }
  });
  if (!response.ok || !response.body) throw new Error(`SAM public extract HTTP ${response.status}`);
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let bytes = 0;
  while (true) {
    const next = await reader.read();
    if (next.done) break;
    bytes += next.value.byteLength;
    parser.addBytes(next.value.byteLength);
    const stop = parser.push(decoder.decode(next.value, { stream: true }));
    if (stop || bytes >= options.maxBytes) {
      await reader.cancel();
      parser.finish();
      if (bytes >= options.maxBytes && parser.stats().stopped === "eof") parser.markStopped("bytes");
      return parser.stats();
    }
  }
  parser.finish();
  return parser.stats();
}
__name(pullSamPublicExtract, "pullSamPublicExtract");
function createContractOpportunityParser(options) {
  const allow = new Set(options.naics);
  const records = [];
  const seen = /* @__PURE__ */ new Set();
  let header = null;
  let field = "";
  let row = [];
  let inQuotes = false;
  let scannedRows = 0;
  let matched = 0;
  let stale = 0;
  let bytes = 0;
  let stopped = "eof";
  const emit = /* @__PURE__ */ __name((cells) => {
    if (!header) {
      header = cells.map((cell) => cell.trim());
      return;
    }
    if (cells.every((cell) => !cell.trim())) return;
    scannedRows += 1;
    const record = {};
    header.forEach((name, index) => {
      record[name] = cells[index] ?? "";
    });
    const posted = Date.parse((record.PostedDate ?? "").trim().replace(" ", "T") + "Z");
    if (!Number.isNaN(posted) && posted < options.windowStartMs) {
      stale += 1;
      if (stale >= 40) stopped = "window";
      return;
    }
    stale = 0;
    const naics = (record.NaicsCode ?? "").trim();
    const active = (record.Active ?? "").trim().toLowerCase();
    if (allow.size && !allow.has(naics)) return;
    if (active && !/^(yes|true|y)$/i.test(active)) return;
    const noticeId = (record.NoticeId ?? "").trim();
    const title = (record.Title ?? "").trim();
    if (!noticeId || !title || seen.has(noticeId)) return;
    seen.add(noticeId);
    const loaded = opportunityFromFoundry(toSamShape(record), { origin: "sam-public", retrievedAt: options.retrievedAt });
    records.push(loaded);
    matched += 1;
    if (matched >= options.limit) stopped = "matches";
  }, "emit");
  const push = /* @__PURE__ */ __name((chunk) => {
    for (let index = 0; index < chunk.length; index += 1) {
      const char = chunk[index];
      if (inQuotes) {
        if (char === '"') {
          if (chunk[index + 1] === '"') {
            field += '"';
            index += 1;
          } else inQuotes = false;
        } else field += char;
      } else if (char === '"') inQuotes = true;
      else if (char === ",") {
        row.push(field);
        field = "";
      } else if (char === "\n") {
        row.push(field);
        field = "";
        emit(row);
        row = [];
        if (stopped === "window" || stopped === "matches") return true;
      } else if (char !== "\r") field += char;
    }
    return stopped === "window" || stopped === "matches";
  }, "push");
  return {
    push,
    addBytes(count) {
      bytes += count;
    },
    finish() {
      if (field.length || row.length) {
        row.push(field);
        field = "";
        emit(row);
        row = [];
      }
    },
    markStopped(value) {
      stopped = value;
    },
    stats() {
      return { records, scannedRows, matched, bytes, stopped };
    }
  };
}
__name(createContractOpportunityParser, "createContractOpportunityParser");
function toSamShape(record) {
  const noticeId = record.NoticeId.trim();
  const agency = [record["Department/Ind.Agency"], record["Sub-Tier"], record.Office].map((part) => part?.trim()).filter(Boolean).join(".");
  const link = record.Link?.trim() || `https://sam.gov/workspace/contract/opp/${noticeId}/view`;
  return {
    noticeId,
    title: record.Title.trim(),
    solicitationNumber: record["Sol#"]?.trim() || void 0,
    fullParentPathName: agency,
    postedDate: record.PostedDate?.trim(),
    type: record.Type?.trim(),
    baseType: record.BaseType?.trim(),
    responseDeadLine: record.ResponseDeadLine?.trim() || void 0,
    naicsCode: record.NaicsCode?.trim(),
    classificationCode: record.ClassificationCode?.trim(),
    typeOfSetAsideDescription: record.SetASide?.trim() || record.SetASideCode?.trim(),
    active: record.Active?.trim(),
    uiLink: link,
    description: record.Description?.trim(),
    placeOfPerformance: {
      city: { name: record.PopCity?.trim() },
      state: { code: record.PopState?.trim() },
      zip: record.PopZip?.trim(),
      country: { code: record.PopCountry?.trim() }
    },
    pointOfContact: [{
      fullName: record.PrimaryContactFullname?.trim(),
      email: record.PrimaryContactEmail?.trim(),
      phone: record.PrimaryContactPhone?.trim(),
      type: "primary"
    }]
  };
}
__name(toSamShape, "toSamShape");

// ../src/intake.ts
import { createHash } from "node:crypto";
function normalizeOpportunity(input) {
  const provenance = [...input.provenance].map((source) => ({ ...source, system: source.system.trim(), url: source.url.trim() })).sort((a, b) => `${a.system}:${a.url}`.localeCompare(`${b.system}:${b.url}`));
  return {
    ...input,
    title: compact(input.title),
    issuer: compact(input.issuer),
    jurisdiction: compact(input.jurisdiction),
    summary: compact(input.summary),
    eligibility: unique(input.eligibility.map(compact)),
    requiredRegistrations: unique(input.requiredRegistrations.map(compact)),
    provenance
  };
}
__name(normalizeOpportunity, "normalizeOpportunity");
function hashOpportunity(input) {
  const stable = {
    ...input,
    provenance: input.provenance.map(({ retrievedAt, ...source }) => source)
  };
  return createHash("sha256").update(JSON.stringify(stable)).digest("hex");
}
__name(hashOpportunity, "hashOpportunity");
function compact(value) {
  return value.trim().replace(/\s+/g, " ");
}
__name(compact, "compact");
function unique(values) {
  return [...new Set(values.filter(Boolean))].sort();
}
__name(unique, "unique");

// ../src/edge/store.ts
async function persistOpportunity(db, input) {
  const opportunity = normalizeOpportunity(input.opportunity);
  const canonicalHash = hashOpportunity(opportunity);
  const sourceSystem = opportunity.provenance[0]?.system ?? "unknown";
  const existing = await db.prepare(
    `select event_id, canonical_hash, revision, status, opportunity_json from opportunity_records where source_system = ? and external_id = ?`
  ).bind(sourceSystem, opportunity.externalId).first();
  if (existing?.canonical_hash === canonicalHash) {
    await db.prepare(`update opportunity_records set last_seen_at = ? where event_id = ?`).bind(input.receivedAt, existing.event_id).run();
    return { eventId: existing.event_id, externalId: opportunity.externalId, disposition: "unchanged", canonicalHash, revision: existing.revision };
  }
  const eventId = existing?.event_id ?? opportunity.eventId;
  const revision = (existing?.revision ?? 0) + 1;
  const status = inferStatus(opportunity);
  const disposition = status === "cancelled" ? "cancelled" : status === "awarded" ? "awarded" : existing ? "amended" : "created";
  const changedFields = existing ? diffStored(existing, opportunity) : [];
  const storedOpportunity = { ...opportunity, eventId };
  const opportunityJson = JSON.stringify(storedOpportunity);
  const payload = JSON.stringify({ sourceRunId: input.sourceRunId, receivedAt: input.receivedAt, opportunity: storedOpportunity });
  await db.batch([
    db.prepare(
      `insert into opportunity_records (event_id, external_id, source_system, canonical_hash, revision, status, opportunity_json, first_seen_at, last_seen_at)
       values (?, ?, ?, ?, ?, ?, ?, ?, ?)
       on conflict(source_system, external_id) do update set
         canonical_hash = excluded.canonical_hash,
         revision = excluded.revision,
         status = excluded.status,
         opportunity_json = excluded.opportunity_json,
         last_seen_at = excluded.last_seen_at`
    ).bind(eventId, opportunity.externalId, sourceSystem, canonicalHash, revision, status, opportunityJson, input.receivedAt, input.receivedAt),
    db.prepare(
      `insert into opportunity_revisions (event_id, revision, canonical_hash, change_type, changed_fields, opportunity_json, observed_at)
       values (?, ?, ?, ?, ?, ?, ?)`
    ).bind(eventId, revision, canonicalHash, disposition, JSON.stringify(changedFields), opportunityJson, input.receivedAt),
    db.prepare(
      `insert into intake_outbox (event_type, aggregate_id, payload_json, occurred_at) values (?, ?, ?, ?)`
    ).bind(`opportunity.${disposition}`, eventId, payload, input.receivedAt)
  ]);
  return { eventId, externalId: opportunity.externalId, disposition, canonicalHash, revision };
}
__name(persistOpportunity, "persistOpportunity");
function inferStatus(opportunity) {
  const text2 = `${opportunity.title} ${opportunity.summary}`.toLowerCase();
  if (text2.includes("cancelled") || text2.includes("canceled")) return "cancelled";
  if (text2.includes("award notice") || text2.includes("awarded")) return "awarded";
  if (opportunity.deadline && Date.parse(opportunity.deadline) < Date.now()) return "closed";
  return "active";
}
__name(inferStatus, "inferStatus");
function diffStored(before, after) {
  let previous;
  try {
    previous = JSON.parse(before.opportunity_json);
  } catch {
    return ["opportunity_json"];
  }
  return Object.keys(after).filter((key) => JSON.stringify(previous[key]) !== JSON.stringify(after[key])).map(String);
}
__name(diffStored, "diffStored");

// ../src/edge/index.ts
var MAX_BODY_BYTES = 1048576;
var index_default = {
  fetch(request, env) {
    return handleIntakeRequest(request, env);
  },
  scheduled(_controller, env) {
    return handleScheduledIntake(env).then(() => void 0);
  }
};
async function handleIntakeRequest(request, env) {
  const url = new URL(request.url);
  if (request.method === "GET" && url.pathname === "/health") {
    return json({ ok: true, service: "opportunity-intake", externalActionsBlocked: true });
  }
  if (url.pathname !== "/api/opportunities/ingest") return json({ error: "Not found" }, 404);
  if (request.method !== "POST") return json({ error: "Method not allowed" }, 405);
  if (!await ingestAuthorized(request, env.INGEST_TOKEN)) return json({ error: "Unauthorized" }, 401);
  const body = await readLimitedBody(request);
  if (!body.ok) return json({ error: body.error }, body.status);
  let parsed;
  try {
    parsed = JSON.parse(body.text);
  } catch {
    return json({ error: "Invalid JSON body" }, 400);
  }
  const sourceRunId = request.headers.get("x-source-run-id")?.trim() || "edge-ingest";
  const receivedAt = (/* @__PURE__ */ new Date()).toISOString();
  const loaded = recordsFromFoundryDocument(parsed, { sourceRunId, receivedAt });
  const summary = await persistLoaded(env, loaded.records, loaded.errors.map((error) => ({ message: error.message })), {
    sourceRunId,
    receivedAt,
    secrets: []
  });
  return json(summary, summary.errors.length && !summary.results.length ? 400 : 200);
}
__name(handleIntakeRequest, "handleIntakeRequest");
async function handleScheduledIntake(env, options = {}) {
  const apiKey = env.SAM_GOV_API_KEY?.trim() ?? "";
  const now = options.now ?? /* @__PURE__ */ new Date();
  const receivedAt = now.toISOString();
  const lookback = positive(env.FOUNDRY_INGEST_LOOKBACK_DAYS, 1);
  const to = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const from = new Date(to);
  from.setUTCDate(from.getUTCDate() - lookback);
  const postedFrom = formatSamDate(from);
  const postedTo = formatSamDate(to);
  const naics = parseNaicsList(env.FOUNDRY_INGEST_NAICS);
  const dispositions = parseDispositionList(env.FOUNDRY_INGEST_DISPOSITIONS);
  const records = [];
  const errors = [];
  const seen = /* @__PURE__ */ new Set();
  try {
    const extracted = await pullSamPublicExtract({
      naics,
      windowStartMs: from.getTime(),
      limit: positive(env.FOUNDRY_INGEST_LIMIT, 100),
      maxBytes: positive(env.PUBLIC_EXTRACT_MAX_BYTES, 8e6),
      retrievedAt: receivedAt,
      fetchImpl: options.fetchImpl,
      csvText: options.csvText,
      url: env.SAM_PUBLIC_CSV_URL || SAM_PUBLIC_OPPORTUNITIES_CSV
    });
    for (const record of extracted.records) {
      if (seen.has(record.externalId)) continue;
      seen.add(record.externalId);
      records.push(record);
    }
    console.log(JSON.stringify({ event: "intake.public_extract", scannedRows: extracted.scannedRows, matched: extracted.matched, bytes: extracted.bytes, stopped: extracted.stopped }));
  } catch (error) {
    errors.push({ message: `SAM public extract: ${error instanceof Error ? error.message : String(error)}` });
  }
  if (!apiKey) {
    console.log(JSON.stringify({ event: "intake.sam_api.skipped", reason: "SAM_GOV_API_KEY is not set" }));
  } else {
    const pull = /* @__PURE__ */ __name(async (code) => {
      try {
        const notices = await searchSamGov({
          apiKey,
          postedFrom,
          postedTo,
          limit: positive(env.FOUNDRY_INGEST_LIMIT, 100),
          maxPages: positive(env.SAM_GOV_MAX_PAGES, 5),
          naics: code,
          fetchImpl: options.fetchImpl
        });
        for (const notice of notices) {
          try {
            const loaded = opportunityFromFoundry(notice, { origin: "sam-api", retrievedAt: receivedAt });
            if (seen.has(loaded.externalId)) continue;
            seen.add(loaded.externalId);
            records.push(loaded);
          } catch (error) {
            errors.push({ message: redactSecrets(error instanceof Error ? error.message : String(error), [apiKey]) });
          }
        }
      } catch (error) {
        errors.push({ message: redactSecrets(`SAM.gov NAICS ${code ?? "all"}: ${error instanceof Error ? error.message : String(error)}`, [apiKey]) });
      }
    }, "pull");
    if (!naics.length) await pull();
    else for (const code of naics) await pull(code);
  }
  const summary = await persistLoaded(env, records, errors, {
    sourceRunId: apiKey ? `sam-api:${postedFrom}_to_${postedTo}` : `sam-public:${postedFrom}_to_${postedTo}`,
    receivedAt,
    secrets: [apiKey],
    dispositions,
    naics
  });
  console.log(JSON.stringify({
    event: "intake.cron.completed",
    sourceRunId: summary.sourceRunId,
    loaded: summary.loaded,
    selected: summary.selected,
    skipped: summary.skipped.length,
    results: summary.results.map((result) => ({ externalId: result.externalId, disposition: result.disposition })),
    errors: summary.errors.length
  }));
  return summary;
}
__name(handleScheduledIntake, "handleScheduledIntake");
async function persistLoaded(env, records, preloadErrors, options) {
  const dispositions = options.dispositions ?? parseDispositionList(env.FOUNDRY_INGEST_DISPOSITIONS);
  const naics = options.naics ?? parseNaicsList(env.FOUNDRY_INGEST_NAICS);
  const { selected, skipped } = selectFoundryRecords(records, { dispositions, naics });
  const results = [];
  const errors = [...preloadErrors];
  for (const record of selected) {
    try {
      results.push(await persistOpportunity(env.DB, { sourceRunId: options.sourceRunId, receivedAt: options.receivedAt, opportunity: record.opportunity }));
    } catch (error) {
      errors.push({ externalId: record.externalId, message: redactSecrets(error instanceof Error ? error.message : String(error), options.secrets) });
    }
  }
  return { sourceRunId: options.sourceRunId, loaded: records.length, selected: selected.length, skipped, results, errors };
}
__name(persistLoaded, "persistLoaded");
async function readLimitedBody(request) {
  if (!request.body) return { ok: false, status: 400, error: "Missing body" };
  const reader = request.body.getReader();
  const chunks = [];
  let total = 0;
  while (true) {
    const next = await reader.read();
    if (next.done) break;
    total += next.value.byteLength;
    if (total > MAX_BODY_BYTES) return { ok: false, status: 413, error: "Payload too large" };
    chunks.push(next.value);
  }
  return { ok: true, text: new TextDecoder().decode(concatBytes(chunks)) };
}
__name(readLimitedBody, "readLimitedBody");
function concatBytes(chunks) {
  const out = new Uint8Array(chunks.reduce((sum, chunk) => sum + chunk.byteLength, 0));
  let offset = 0;
  for (const chunk of chunks) {
    out.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return out;
}
__name(concatBytes, "concatBytes");
function positive(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? Math.trunc(parsed) : fallback;
}
__name(positive, "positive");
function json(body, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json; charset=utf-8" } });
}
__name(json, "json");
export {
  index_default as default,
  handleIntakeRequest,
  handleScheduledIntake
};
//# sourceMappingURL=index.js.map
