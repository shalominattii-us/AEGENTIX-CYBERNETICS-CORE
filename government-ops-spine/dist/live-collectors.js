import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { readdir, readFile, stat } from 'node:fs/promises';
import { join, extname } from 'node:path';
import { createHash } from 'node:crypto';
const execFileAsync = promisify(execFile);
const zones = ['OpenClaw', 'Nemotron', 'Hermes', 'Docker', 'Manus'];
const hash = (value) => createHash('sha256').update(JSON.stringify(value)).digest('hex');
export class DockerCapabilityCollector {
    async collect() {
        const { stdout } = await execFileAsync('docker', ['ps', '-a', '--format', '{{json .}}']);
        return stdout.split(/\r?\n/).filter(Boolean).map((line) => {
            const row = JSON.parse(line);
            const name = row.Names ?? row.Image;
            const uri = `docker://${row.Image}/${name}`;
            return { id: `docker:${hash(uri).slice(0, 20)}`, name, tags: tokenize(`${name} ${row.Image} ${row.Ports} ${row.Status}`), maturity: /Up /.test(row.Status ?? '') ? 'deployed' : 'image', evidence: [uri, row.Status].filter(Boolean), executionZones: zones, sourceType: 'docker', sourceUri: uri, description: `Docker container ${name} using image ${row.Image}`, metadata: row, contentHash: hash(row), discoveredAt: new Date().toISOString() };
        });
    }
}
export class GitHubWorkspaceCollector {
    roots;
    constructor(roots) {
        this.roots = roots;
    }
    async collect() {
        const assets = [];
        for (const root of this.roots)
            for (const entry of await safeReadDir(root)) {
                const full = join(root, entry.name);
                if (!entry.isDirectory() || !(await safeStat(join(full, '.git')))?.isDirectory())
                    continue;
                const readme = await readFirst(full, ['README.md', 'README.MD', 'readme.md']);
                assets.push({ id: `github:${hash(full).slice(0, 20)}`, name: entry.name, tags: tokenize(`${entry.name} ${readme ?? ''}`), maturity: 'repository', evidence: [full], executionZones: zones, sourceType: 'github', sourceUri: full, description: readme?.slice(0, 600) ?? `Git repository at ${full}`, metadata: { path: full }, contentHash: hash({ full, readme }), discoveredAt: new Date().toISOString() });
            }
        return assets;
    }
}
export class FilesystemDocumentCollector {
    roots;
    maxFiles;
    constructor(roots, maxFiles = 500) {
        this.roots = roots;
        this.maxFiles = maxFiles;
    }
    async collect() { const assets = []; for (const root of this.roots)
        await walk(root, async (path) => { if (assets.length >= this.maxFiles)
            return; const extension = extname(path).toLowerCase(); if (!['.md', '.txt', '.json', '.yaml', '.yml', '.pdf', '.docx', '.pptx', '.step', '.stp', '.dwg'].includes(extension))
            return; let preview = ''; if (['.md', '.txt', '.json', '.yaml', '.yml'].includes(extension))
            preview = (await readFile(path, 'utf8')).slice(0, 1200); const sourceType = extension === '.step' || extension === '.stp' || extension === '.dwg' ? 'cad' : 'document'; assets.push({ id: `document:${hash(path).slice(0, 20)}`, name: path.split(/[\\/]/).pop() ?? path, tags: tokenize(`${path} ${preview}`), maturity: 'documented', evidence: [path], executionZones: zones, sourceType, sourceUri: path, description: preview || `${extension.slice(1).toUpperCase()} asset`, metadata: { path, extension }, contentHash: hash({ path, preview }), discoveredAt: new Date().toISOString() }); }); return assets; }
}
async function walk(root, visit) { for (const entry of await safeReadDir(root)) {
    const full = join(root, entry.name);
    if (entry.isDirectory())
        await walk(full, visit);
    else
        await visit(full);
} }
async function safeReadDir(path) { try {
    return await readdir(path, { withFileTypes: true });
}
catch {
    return [];
} }
async function safeStat(path) { try {
    return await stat(path);
}
catch {
    return undefined;
} }
async function readFirst(root, names) { for (const name of names) {
    try {
        return await readFile(join(root, name), 'utf8');
    }
    catch { }
} return undefined; }
function tokenize(value) { return [...new Set((value.toLowerCase().match(/[a-z0-9][a-z0-9._-]{2,}/g) ?? []).filter(v => v.length < 64))].slice(0, 80); }
