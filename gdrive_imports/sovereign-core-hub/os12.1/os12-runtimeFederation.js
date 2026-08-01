// os12-runtimeFederation.js
const registry = new Map();

function registerRuntime(name, info) {
  registry.set(name, { name, info, updatedAt: Date.now() });
  console.log('[OS12.1][FEDERATION] Registered:', name, info);
}

function listRuntimes() {
  return Array.from(registry.values());
}

async function callRuntime(name, method, payload) {
  const rt = registry.get(name);
  if (!rt || !rt.info || typeof rt.info.handler !== 'function') {
    throw new Error(`Runtime ${name} unavailable`);
  }
  return rt.info.handler({ method, payload });
}

module.exports = { registerRuntime, listRuntimes, callRuntime };
