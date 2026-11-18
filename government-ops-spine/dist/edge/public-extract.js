import { opportunityFromFoundry } from '../foundry-bridge.js';
export const SAM_PUBLIC_OPPORTUNITIES_CSV = 'https://sam.gov/api/prod/fileextractservices/v1/api/download/Contract%20Opportunities/datagov/ContractOpportunitiesFullCSV.csv?privacy=Public';
export async function pullSamPublicExtract(options) {
    const parser = createContractOpportunityParser(options);
    if (options.csvText !== undefined) {
        parser.push(options.csvText);
        parser.finish();
        return parser.stats();
    }
    const fetchImpl = options.fetchImpl ?? fetch;
    const response = await fetchImpl(options.url ?? SAM_PUBLIC_OPPORTUNITIES_CSV, {
        redirect: 'follow',
        headers: { accept: 'text/csv,*/*', 'user-agent': 'gov-opportunity-intake/1.0' }
    });
    if (!response.ok || !response.body)
        throw new Error(`SAM public extract HTTP ${response.status}`);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let bytes = 0;
    while (true) {
        const next = await reader.read();
        if (next.done)
            break;
        bytes += next.value.byteLength;
        parser.addBytes(next.value.byteLength);
        const stop = parser.push(decoder.decode(next.value, { stream: true }));
        if (stop || bytes >= options.maxBytes) {
            await reader.cancel();
            parser.finish();
            if (bytes >= options.maxBytes && parser.stats().stopped === 'eof')
                parser.markStopped('bytes');
            return parser.stats();
        }
    }
    parser.finish();
    return parser.stats();
}
function createContractOpportunityParser(options) {
    const allow = new Set(options.naics);
    const records = [];
    const seen = new Set();
    let header = null;
    let field = '';
    let row = [];
    let inQuotes = false;
    let scannedRows = 0;
    let matched = 0;
    let stale = 0;
    let bytes = 0;
    let stopped = 'eof';
    const emit = (cells) => {
        if (!header) {
            header = cells.map((cell) => cell.trim());
            return;
        }
        if (cells.every((cell) => !cell.trim()))
            return;
        scannedRows += 1;
        const record = {};
        header.forEach((name, index) => { record[name] = cells[index] ?? ''; });
        const posted = Date.parse((record.PostedDate ?? '').trim().replace(' ', 'T') + 'Z');
        if (!Number.isNaN(posted) && posted < options.windowStartMs) {
            stale += 1;
            if (stale >= 40)
                stopped = 'window';
            return;
        }
        stale = 0;
        const naics = (record.NaicsCode ?? '').trim();
        const active = (record.Active ?? '').trim().toLowerCase();
        if (allow.size && !allow.has(naics))
            return;
        if (active && !/^(yes|true|y)$/i.test(active))
            return;
        const noticeId = (record.NoticeId ?? '').trim();
        const title = (record.Title ?? '').trim();
        if (!noticeId || !title || seen.has(noticeId))
            return;
        seen.add(noticeId);
        const loaded = opportunityFromFoundry(toSamShape(record), { origin: 'sam-public', retrievedAt: options.retrievedAt });
        records.push(loaded);
        matched += 1;
        if (matched >= options.limit)
            stopped = 'matches';
    };
    const push = (chunk) => {
        for (let index = 0; index < chunk.length; index += 1) {
            const char = chunk[index];
            if (inQuotes) {
                if (char === '"') {
                    if (chunk[index + 1] === '"') {
                        field += '"';
                        index += 1;
                    }
                    else
                        inQuotes = false;
                }
                else
                    field += char;
            }
            else if (char === '"')
                inQuotes = true;
            else if (char === ',') {
                row.push(field);
                field = '';
            }
            else if (char === '\n') {
                row.push(field);
                field = '';
                emit(row);
                row = [];
                if (stopped === 'window' || stopped === 'matches')
                    return true;
            }
            else if (char !== '\r')
                field += char;
        }
        return stopped === 'window' || stopped === 'matches';
    };
    return {
        push,
        addBytes(count) { bytes += count; },
        finish() {
            if (field.length || row.length) {
                row.push(field);
                field = '';
                emit(row);
                row = [];
            }
        },
        markStopped(value) { stopped = value; },
        stats() { return { records, scannedRows, matched, bytes, stopped }; }
    };
}
function toSamShape(record) {
    const noticeId = record.NoticeId.trim();
    const agency = [record['Department/Ind.Agency'], record['Sub-Tier'], record.Office].map((part) => part?.trim()).filter(Boolean).join('.');
    const link = record.Link?.trim() || `https://sam.gov/workspace/contract/opp/${noticeId}/view`;
    return {
        noticeId,
        title: record.Title.trim(),
        solicitationNumber: record['Sol#']?.trim() || undefined,
        fullParentPathName: agency,
        postedDate: record.PostedDate?.trim(),
        type: record.Type?.trim(),
        baseType: record.BaseType?.trim(),
        responseDeadLine: record.ResponseDeadLine?.trim() || undefined,
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
                type: 'primary'
            }]
    };
}
