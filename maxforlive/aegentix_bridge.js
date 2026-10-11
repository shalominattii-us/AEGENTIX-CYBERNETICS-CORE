/* AEGENTIX CyberDAW Max-for-Live bridge reference.
 *
 * Host-side protocol adapter. Production authorization belongs to AEGENTIX's
 * external gate, not this device. Map handlers to real Max objects in a licensed
 * Ableton environment during integration validation.
 */

autowatch = 1;
inlets = 1;
outlets = 1;

var bridgeVersion = "1.0";
var bridgeSource = "aegentix";
var bridgeCounter = 0;

function nextId() {
    bridgeCounter += 1;
    return "m4l-" + bridgeCounter;
}

function now() {
    return new Date().toISOString();
}

function emit(name, args, target) {
    if (args === undefined) {
        args = {};
    }
    if (target === undefined) {
        target = null;
    }
    outlet(0, JSON.stringify({
        version: bridgeVersion,
        id: nextId(),
        timestamp: now(),
        source: bridgeSource,
        command: {
            name: String(name),
            target: target,
            args: args
        }
    }));
}

function transport(action) {
    emit("transport", { action: String(action) });
}

function tempo(bpm) {
    emit("tempo", { bpm: Number(bpm) });
}

function scene(index) {
    emit("scene", { index: Number(index) });
}

function clip(track, slot, action) {
    emit("clip", { track: Number(track), slot: Number(slot), action: String(action) });
}

function device(track, deviceIndex) {
    emit("device", { track: Number(track), device: Number(deviceIndex) });
}

function parameter(track, deviceIndex, parameterIndex, value) {
    emit("parameter", {
        track: Number(track),
        device: Number(deviceIndex),
        parameter: Number(parameterIndex),
        value: Number(value)
    });
}

function telemetry(payload) {
    emit("telemetry", payload === undefined ? {} : payload);
}

function record(action, target, args) {
    var envelopeArgs = { action: String(action) };
    if (args && typeof args === "object") {
        for (var key in args) {
            envelopeArgs[key] = args[key];
        }
    }
    emit("record", envelopeArgs, target === undefined ? null : target);
}

function stop(reason) {
    emit("stop", { reason: reason === undefined ? "aegentix_emergency_stop" : String(reason) });
}
