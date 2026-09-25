// sovereign-claw.js - AEGENTIX SOVEREIGN CLAW (FIXED)
// Full ROG Ally X utilization - ALL CORES, ALL RAM, MAXIMUM POWER

const fs = require('fs');
const os = require('os');
const { exec, spawn, execSync } = require('child_process');
const http = require('http');

console.log('');
console.log('='.repeat(60));
console.log('  SOVEREIGN CLAW ACTIVATED');
console.log('  Full ROG Ally X Utilization');
console.log('  ALL CORES - ALL RAM - MAXIMUM POWER');
console.log('='.repeat(60));
console.log('');

// ============================================================
// HARDWARE DETECTION
// ============================================================
const CLAW = {
    cores: os.cpus().length,
    totalRAM: os.totalmem() / (1024**3),
    freeRAM: os.freemem() / (1024**3),
    platform: os.platform(),
    arch: os.arch(),
    hostname: os.hostname()
};

console.log('HARDWARE DETECTED:');
console.log('  ---------------------------------------------');
console.log('  CPU Cores:     ' + CLAW.cores + ' (AMD Ryzen AI Z2 Extreme)');
console.log('  Total RAM:     ' + CLAW.totalRAM.toFixed(1) + ' GB');
console.log('  Free RAM:      ' + CLAW.freeRAM.toFixed(1) + ' GB');
console.log('  Platform:      ' + CLAW.platform);
console.log('  Architecture:  ' + CLAW.arch);
console.log('');

// ============================================================
// CONFIGURATION
// ============================================================
const CONFIG = {
    maxWorkers: CLAW.cores * 4,
    memoryLimit: Math.floor(CLAW.freeRAM * 0.95),
    scanInterval: 2000,
    batchSize: 10,
    powerMode: 'maximum'
};

console.log('CONFIGURATION:');
console.log('  ---------------------------------------------');
console.log('  Max Workers:   ' + CONFIG.maxWorkers);
console.log('  Memory Limit:  ' + CONFIG.memoryLimit + ' GB');
console.log('  Scan Interval: ' + CONFIG.scanInterval/1000 + 's');
console.log('  Batch Size:    ' + CONFIG.batchSize);
console.log('  Power Mode:    ' + CONFIG.powerMode);
console.log('');

// ============================================================
// SOVEREIGN CLAW ENGINE
// ============================================================
class SovereignClaw {
    constructor() {
        this.tasks = [];
        this.running = 0;
        this.completed = 0;
        this.startTime = Date.now();
        this.cycleCount = 0;
        this.maxWorkers = CONFIG.maxWorkers;
        this.errors = 0;
        this.totalTasks = 0;
        this.avgTime = 0;
    }
    
    addTask(task) {
        this.tasks.push(task);
        this.process();
    }
    
    process() {
        while (this.running < this.maxWorkers && this.tasks.length > 0) {
            const task = this.tasks.shift();
            this.running++;
            this.executeTask(task);
        }
    }
    
    executeTask(task) {
        const start = Date.now();
        const worker = spawn('node', ['-e', task]);
        let output = '';
        
        worker.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        worker.stderr.on('data', (data) => {
            output += data.toString();
        });
        
        worker.on('close', (code) => {
            this.running--;
            this.completed++;
            this.totalTasks++;
            const time = Date.now() - start;
            this.avgTime = (this.avgTime * (this.totalTasks - 1) + time) / this.totalTasks;
            if (code !== 0) this.errors++;
            
            console.log('  Worker ' + this.completed + ' complete (' + time + 'ms)');
            this.process();
        });
    }
    
    getStats() {
        const uptime = (Date.now() - this.startTime) / 1000;
        return {
            running: this.running,
            total: this.maxWorkers,
            completed: this.completed,
            pending: this.tasks.length,
            totalTasks: this.totalTasks,
            avgTime: Math.round(this.avgTime) + 'ms',
            errors: this.errors,
            cycles: this.cycleCount,
            uptime: Math.floor(uptime / 60) + 'm ' + Math.floor(uptime % 60) + 's',
            freeRAM: (os.freemem() / (1024**3)).toFixed(1) + ' GB'
        };
    }
    
    cycle() {
        this.cycleCount++;
        const tasks = this.generateTasks();
        for (const task of tasks) {
            this.addTask(task);
        }
        return this.getStats();
    }
    
    generateTasks() {
        const tasks = [];
        
        // Task 1: Service health check
        tasks.push('const http = require(\'http\'); const ports = [3000,8080,8090,7070,7071,7072,7073]; let h = 0; for (const p of ports) { try { const req = http.get(\'http://localhost:\' + p + \'/health\', (r) => { if (r.statusCode === 200) h++; }); req.on(\'error\', () => {}); req.end(); } catch {} } console.log(\'Services: \' + h + \'/7 healthy\');');
        
        // Task 2: System metrics
        tasks.push('const os = require(\'os\'); const mem = os.freemem() / (1024**3); const total = os.totalmem() / (1024**3); const load = os.loadavg(); console.log(\'RAM: \' + mem.toFixed(1) + \'GB free, Load: \' + load[0].toFixed(2) + \', \' + load[1].toFixed(2) + \', \' + load[2].toFixed(2));');
        
        // Task 3: File count
        tasks.push('const fs = require(\'fs\'); const path = require(\'path\'); let c = 0; function scan(d) { try { const items = fs.readdirSync(d); for (const i of items) { if ([\'node_modules\',\'.git\'].includes(i)) continue; const f = path.join(d, i); if (fs.statSync(f).isDirectory()) { scan(f); } else if (i.match(/\\.(js|ts|json|yml|yaml)$/)) { c++; } } } catch {} } scan(\'.\'); console.log(\'Files: \' + c);');
        
        // Task 4: Docker status
        tasks.push('const { execSync } = require(\'child_process\'); try { const r = execSync(\'docker compose ps --format json\', { encoding: \'utf-8\', stdio: \'pipe\' }); const s = JSON.parse(r); const run = s.filter(x => x.State === \'running\').length; console.log(\'Docker: \' + run + \'/7 running\'); } catch { console.log(\'Docker: 0/7 running\'); }');
        
        return tasks;
    }
}

// ============================================================
// ACTIVATE CLAW
// ============================================================
const claw = new SovereignClaw();

console.log('SOVEREIGN CLAW ACTIVATED');
console.log('='.repeat(60));
console.log('');

// ============================================================
// WEB DASHBOARD
// ============================================================
const server = http.createServer((req, res) => {
    const stats = claw.getStats();
    let html = '';
    html += '<!DOCTYPE html>\n';
    html += '<html><head><title>Sovereign Claw</title>\n';
    html += '<style>body{background:#0a0a0f;color:#00ff88;font-family:"Courier New";padding:40px}h1{font-size:3em;color:#00ff88;text-shadow:0 0 30px #00ff8844}.grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:15px;margin:20px 0}.card{background:#111;border:1px solid #00ff8833;border-radius:10px;padding:20px}.card .value{font-size:2em;color:#00ff88}.card .label{color:#666;font-size:0.8em;text-transform:uppercase}.footer{margin-top:40px;color:#444;border-top:1px solid #222;padding-top:20px}.status{color:#00ff88;font-size:1.2em}</style>\n';
    html += '</head><body>\n';
    html += '<h1>🦞 Sovereign Claw</h1>\n';
    html += '<div class="status">⚡ FULL POWER MODE</div>\n';
    html += '<div class="grid">\n';
    html += '<div class="card"><div class="label">Workers</div><div class="value">' + stats.running + '/' + stats.total + '</div></div>\n';
    html += '<div class="card"><div class="label">Tasks</div><div class="value">' + stats.totalTasks + '</div></div>\n';
    html += '<div class="card"><div class="label">Cycles</div><div class="value">' + stats.cycles + '</div></div>\n';
    html += '<div class="card"><div class="label">RAM Free</div><div class="value">' + stats.freeRAM + '</div></div>\n';
    html += '<div class="card"><div class="label">Uptime</div><div class="value">' + stats.uptime + '</div></div>\n';
    html += '<div class="card"><div class="label">Errors</div><div class="value" style="color:#00ff88;">' + stats.errors + '</div></div>\n';
    html += '</div>\n';
    html += '<div class="footer">🦞 Sovereign Claw · ROG Ally X · Full Power</div>\n';
    html += '</body></html>\n';
    
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
});

const CLAW_PORT = 3003;
server.listen(CLAW_PORT, () => {
    console.log('🌐 Dashboard: http://localhost:' + CLAW_PORT);
    console.log('');
});

// ============================================================
// CONTINUOUS CYCLES
// ============================================================
console.log('🔄 SOVEREIGN CLAW CYCLES STARTING...');
console.log('='.repeat(60));
console.log('');

function runCycle() {
    const stats = claw.cycle();
    console.log('');
    console.log('🦞 CYCLE ' + stats.cycles + ' - ' + new Date().toISOString());
    console.log('  Workers: ' + stats.running + '/' + stats.total + ' running');
    console.log('  Tasks: ' + stats.totalTasks + ' processed');
    console.log('  RAM: ' + stats.freeRAM);
    console.log('  Uptime: ' + stats.uptime);
    console.log('  Errors: ' + stats.errors);
}

// Run first cycle
runCycle();

// Run every 2 seconds
setInterval(runCycle, CONFIG.scanInterval);

// Keep alive
process.on('SIGINT', () => {
    console.log('');
    console.log('🦞 Sovereign Claw shutting down...');
    const stats = claw.getStats();
    console.log('Final: ' + stats.totalTasks + ' tasks, ' + stats.cycles + ' cycles, ' + stats.errors + ' errors');
    server.close(() => process.exit(0));
});
