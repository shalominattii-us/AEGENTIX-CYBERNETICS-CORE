# Ableton integration brief

## What CyberDAW is

AEGENTIX CyberDAW is a supervisory integration layer around a DAW performance environment. Orbital owns production state and authorization; Swarm coordinates cues and production tasks; host adapters expose capabilities from Ableton, OBS, audio, recording, and streaming systems.

## Intended Ableton integration

The production adapter expects:

1. Ableton Live Suite.
2. Max for Live enabled.
3. An AEGENTIX Max-for-Live bridge device.
4. A bidirectional, authenticated bridge path for commands and telemetry.
5. Functional verification of transport, tempo, scenes, clips, devices, parameters, and telemetry.

The bridge protocol is deliberately host-neutral. A production integration can map the protocol to the actual supported Ableton/Max APIs without coupling Orbital to a particular host version.

## Demonstration environment

The existing Trial installation can be used to demonstrate the architecture and development workflows. It does not unlock production authorization.

## What we want Ableton to evaluate

- Control/telemetry contract.
- Max-for-Live bridge architecture.
- Deterministic supervisory state machine.
- Cue/scene orchestration.
- Safety and fail-closed production gate.
- Offline-first operation.
- Separation of PA/master and broadcast/recording paths.
- Extension points for multitrack/stem workflows.

This repository is a proof-of-concept integration package, not a claim that an unverified Trial environment is production-ready.
