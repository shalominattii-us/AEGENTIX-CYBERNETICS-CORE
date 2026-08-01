// =====================================================
//   SOVEREIGN OS‑12.1 TEST HARNESS
//   Federation + Metrics Validation
// =====================================================

const http = require('http');
const { listRuntimes, callRuntime } = require('./os12.1/os12-runtimeFederation');

async function testFederation() {
  console.log("\n=== FEDERATION RUNTIMES ===");
  console.log(listRuntimes());

  console.log("\n=== RPC TEST ===");
  try {
    const res = await callRuntime('aegentis-vr', 'ping', { msg: 'hello' });
    console.log("RPC OK:", res);
  } catch (e) {
    console.log("RPC ERROR:", e.message);
  }
}

async function testMetrics(port, label) {
  return new Promise(resolve => {
    http.get(`http://localhost:${port}/metrics`, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        console.log(`\n=== METRICS: ${label} ===`);
        console.log(data);
        resolve();
      });
    }).on('error', err => {
      console.log(`Metrics error (${label}):`, err.message);
      resolve();
    });
  });
}

(async () => {
  await testFederation();
  await testMetrics(7777, 'Aegentis VR');
  await testMetrics(3000, 'Dashboard');
  await testMetrics(8844, 'Agentic AI');
  await testMetrics(9229, 'Destiny');
})();
