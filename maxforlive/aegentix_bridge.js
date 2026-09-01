/* AEGENTIX CyberDAW Max-for-Live bridge reference.
 *
 * This is intentionally a small, host-side protocol adapter. Production
 * authorization belongs to AEGENTIX's external gate, not this device.
 * Map these handlers to the actual Max objects/transport API in the licensed
 * Ableton environment during integration validation.
 */

autowatch = 1;
inlets = 1;
outlets = 1;

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

function stop() {
    emit("stop", { reason: "aegentix_emergency_stop" });
}

function emit(name, args) {
    outlet(0, JSON.stringify({
        version: "1.0",
        source: "aegentix-m4l",
        command: { name: name, args: args }
    }));
}
