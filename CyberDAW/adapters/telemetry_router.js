/**
 * AEGENTIX CyberDAW — Telemetry Router (node.script for Max for Live)
 *
 * Listens for scene/clip selection events from the Max patcher's live.observer
 * and POSTs HMAC-signed JSON payloads to the local AEGENTIS AI Runtime layer.
 *
 * Flow: live.observer → node.script → HTTP POST → multi-llm-runtime (/complete)
 *       → cognitive_bus.py append_event → JSONL stream → Cyberdaw gate checkpoint
 *
 * Port 8000 = local multi-llm-runtime (verified live).
 * Port 8004 = legacy runtime-prime placeholder (portal_main.py upstream config).
 *           Use 8000 for local dev; swap to 8004 when portal_main proxies in prod.
 */

const http = require("http");
const https = require("https");
const crypto = require("crypto");

// ── Configuration ──────────────────────────────────────────────────────────
const RUNTIME_HOST = process.env.RUNTIME_HOST || "127.0.0.1";
const RUNTIME_PORT = parseInt(process.env.RUNTIME_PORT || "8000", 10);
const RUNTIME_PATH = "/telemetry";
const ORCHESTRATOR  = "openrouter-ori-harness";
const MODEL         = "meta-llama/llama-3.1-70b-instruct";
const SECRET_KEY    = Buffer.from("AEGENTIX_EOC_PRIME_LOCK", "utf-8");

// ── Max API ────────────────────────────────────────────────────────────────
// node.script in Max exposes `Max` globally for posting messages back to the patcher.
const Max = typeof Max !== "undefined" ? Max : {
    post(msg) { console.log("[node.script]", msg); }
};

// ── Helpers ────────────────────────────────────────────────────────────────

function generateHMAC(payload) {
    const payloadBytes = JSON.stringify(payload).replace(/\u0000/g, "").slice(0, -1);
    // JSON.stringify adds no trailing newline; we sign the canonical JSON.
    const canonical = JSON.stringify(payload);
    return crypto.createHmac("sha256", SECRET_KEY).update(canonical).digest("hex");
}

function buildTelemetryPayload(eventType, metrics, sceneIndex) {
    const timestamp = Date.now() / 1000;
    const payload = {
        version: "ENGINE-STACK-1.0.0",
        timestamp,
        event: eventType,
        metrics: Object.freeze(metrics),
        orchestrator: ORCHESTRATOR,
        model: MODEL,
        integrity_score: 100,
        source: "cyberdaw-amxd",
        gate_checkpoint: true,
    };
    payload.signature = generateHMAC(payload);
    return payload;
}

function postToRuntime(payload, callback) {
    const body = JSON.stringify(payload);
    const options = {
        hostname: RUNTIME_HOST,
        port: RUNTIME_PORT,
        path: RUNTIME_PATH,
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(body),
            "X-CyberDAW-Source": "amxd-telemetry-router",
        },
    };

    const req = http.request(options, (res) => {
        let data = "";
        res.on("data", (chunk) => { data += chunk; });
        res.on("end", () => {
            let result = null;
            try { result = JSON.parse(data); } catch (_) { result = { raw: data }; }
            callback(null, res.statusCode, result);
        });
    });

    req.on("error", (e) => { callback(e, null, null); });
    req.write(body);
    req.end();
}

// ── Event handlers ─────────────────────────────────────────────────────────

function handleSceneSelection(sceneIndex, sceneName) {
    const payload = buildTelemetryPayload(
        "SCENE_SELECTION_ACTIVE",
        {
            scene_index: sceneIndex,
            scene_name: sceneName || `Scene ${sceneIndex}`,
            selection_state: "STABLE_VERIFIED",
            timestamp_ms: Date.now(),
        },
        sceneIndex
    );

    Max.post(`[CYBERDAW] Scene ${sceneIndex} selected → committing telemetry to runtime on :${RUNTIME_PORT}`);

    postToRuntime(payload, (err, statusCode, result) => {
        if (err) {
            Max.post(`[CYBERDAW ERROR] Portal bridge drop: ${err.message}`);
            Max.post(`[GATE] Status remains fail-closed. Blocker not cleared.`);
            return;
        }
        if (statusCode === 200 && result && result.ok) {
            Max.post(`[CYBERDAW] Telemetry committed. Gate checkpoint SCENE_SELECTION_ACTIVE fired.`);
            Max.post(`[GATE] Runtime response: backend=${result.backend}, model=${result.model}, tokens=${result.tokens}`);
        } else {
            Max.post(`[CYBERDAW] Runtime returned non-ok: ${JSON.stringify(result)}`);
            Max.post(`[GATE] Blocker held — runtime did not confirm.`);
        }
    });
}

function handleClipLaunch(trackId, clipName, sceneIndex) {
    const payload = buildTelemetryPayload(
        "CLIP_LAUNCH_EVENT",
        {
            track_id: trackId,
            clip_name: clipName,
            scene_index: sceneIndex,
            launch_state: "ACTIVE",
            timestamp_ms: Date.now(),
        },
        sceneIndex
    );

    Max.post(`[CYBERDAW] Clip "${clipName}" launched on track ${trackId} → committing telemetry.`);

    postToRuntime(payload, (err, statusCode, result) => {
        if (err) {
            Max.post(`[CYBERDAW ERROR] Clip telemetry drop: ${err.message}`);
            return;
        }
        if (statusCode === 200 && result && result.ok) {
            Max.post(`[CYBERDAW] Clip launch telemetry committed. Checkpoint CLIP_LAUNCH_EVENT fired.`);
        } else {
            Max.post(`[CYBERDAW] Clip telemetry not confirmed by runtime.`);
        }
    });
}

// ── Max node.script message dispatch ──────────────────────────────────────
// Messages arrive via the node.script inlet as function calls on the global scope.
// The Max patcher sends: { sceneIndex, sceneName } on scene selection.
// Adapt this to match whatever the live.observer outputs in your patcher.

function onSceneChange(data) {
    // data can be a number (scene index) or an object with sceneIndex/sceneName
    const sceneIndex = typeof data === "number" ? data : (data && data.sceneIndex);
    const sceneName  = (data && data.sceneName) || null;
    if (sceneIndex !== undefined && sceneIndex !== null) {
        handleSceneSelection(sceneIndex, sceneName);
    }
}

function onClipLaunch(data) {
    if (data && data.trackId !== undefined) {
        handleClipLaunch(data.trackId, data.clipName, data.sceneIndex);
    }
}

// ── Logging / readiness ────────────────────────────────────────────────────
Max.post(`[CYBERDAW] Telemetry Router initialized. RUNTIME=${RUNTIME_HOST}:${RUNTIME_PORT}`);
Max.post(`[CYBERDAW] Orchestrator=${ORCHESTRATOR}, Model=${MODEL}`);
Max.post(`[CYBERDAW] Waiting for scene selection events from live.observer...`);
