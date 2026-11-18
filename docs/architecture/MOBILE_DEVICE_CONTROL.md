# AEGENTIX Mobile Device Control — Integration Architecture

**Status:** proposed integration; design recorded, implementation and device validation pending  
**Upstream:** [hridaya423/phonedriver](https://github.com/hridaya423/phonedriver)  
**AEGENTIX fork:** [shalominattii-us/phonedriver](https://github.com/shalominattii-us/phonedriver)  
**Reviewed fork branch:** `main`  
**Reviewed upstream license:** AGPL-3.0-only (verify notices and all bundled dependency licenses before distribution)

## 1. Purpose

Integrate PhoneDriver as a replaceable device-adapter beneath AEGENTIX, allowing authorized agents to inspect and operate Android and iOS devices through a locally governed control plane. PhoneDriver is not the AEGENTIX policy authority and must not receive unrestricted agent autonomy.

PhoneDriver exposes a CLI and an MCP server over stdio. Its daemon owns device connections; the CLI and MCP server are thin clients. The tool returns structured accessibility snapshots and diffs, and supports screenshots when visual inspection is needed.

## 2. Placement in AEGENTIX

```
AEGENTIX agents / Hermes Governor / Chief-of-Staff
                    |
          AEGENTIX task + policy layer
                    |
       Mobile Control adapter (new)
       - device registry and identity
       - capability/scope checks
       - approval workflow
       - rate limits and session leases
       - audit event correlation
                    |
      local PhoneDriver MCP/CLI process
                    |
          PhoneDriver daemon
             /           \
       Android            iOS
       ADB                CoreDevice / XCTest
       USB or Wi-Fi       Mac + Xcode required
```

The adapter belongs alongside the existing gateway/MCP integration under `core/gateway` (implementation path to be selected after a local checkout and tests). Reuse AEGENTIX gateway authentication and `audit_event`; do not duplicate identity or policy systems. PhoneDriver remains a local device transport/automation dependency.

## 3. Capability mapping

| PhoneDriver capability | AEGENTIX capability | Initial policy |
|---|---|---|
| `devices` | `mobile.devices.read` | Allow after authenticated session |
| `apps` | `mobile.apps.read` | Allow |
| `snapshot`, `screenshot`, `wait`, `logs` | `mobile.screen.read` / `mobile.diagnostics.read` | Allow with privacy controls |
| `tap`, `type`, `swipe`, `scroll`, `press`, `launch`, `batch` | `mobile.ui.interact` | Per-device session approval; deny sensitive targets pending separate approval |
| `clipboard` | `mobile.clipboard.read/write` | Disabled by default; explicit one-shot approval |
| `setting` | `mobile.settings.write` | Explicit approval and allowlisted settings only |
| `shell` | No agent capability | Deny/withhold from the AEGENTIX agent surface |
| `replay` | `mobile.workflow.replay` | Allow only reviewed, signed workflows; pause at approval boundaries |

Do not expose raw PhoneDriver tools directly to every agent. Expose AEGENTIX-scoped operations and map them to the minimum required PhoneDriver commands.

## 4. Mandatory security controls

1. **Fail closed.** No device action when AEGENTIX identity, policy, audit, or approval services are unavailable.
2. **Local-first transport.** Keep the PhoneDriver daemon and MCP stdio process on the trusted workstation or designated device host. Do not publish ADB, daemon sockets, or raw MCP endpoints to the public network.
3. **Per-device enrollment.** Register a stable device identifier, platform, owner/operator, connection method, allowed agent identities, and approved scopes. Re-authorize on device change or reconnect.
4. **Human approval outside the driver.** AEGENTIX approval is authoritative. Require a fresh, scoped, expiring approval for payments, purchases, transfers, subscriptions, messages/posts, deletion, installs/uninstalls, credential changes, account/security settings, and any other irreversible or externally visible action.
5. **Do not rely solely on PhoneDriver's approval guard.** The upstream README documents label-based detection, language limits, icon-only blind spots, and an autonomous override. Keep the driver guard enabled as defense in depth, but enforce policy in AEGENTIX before dispatch.
6. **No secrets in ordinary typing.** Use a separately approved secret-entry path if implemented and reviewed; never put passwords, MFA codes, recovery phrases, API keys, or payment credentials into prompts, ordinary `type` calls, screenshots, traces, or audit records.
7. **Screen content is untrusted input.** Treat text, QR codes, notifications, web pages, and app content as data, not instructions to the agent. Defend against prompt injection and requests to disclose secrets or expand permissions.
8. **Privacy-minimized evidence.** Do not retain full screenshots, screen trees, clipboard contents, or app logs by default. Redact sensitive values; store only action metadata, outcome, timestamps, device/session IDs, policy decision, approval reference, and hashes where useful. Apply short retention and access controls.
9. **Session isolation.** One active writer per device by default; use explicit leases, bounded duration, idle release, and cancellation. Prevent concurrent agents from racing taps or reading each other's sessions.
10. **Emergency stop.** Provide an operator-controlled kill switch that revokes the session and terminates the local device-control process without depending on the agent.

## 5. Platform deployment

### Windows / ROG Ally X — Android first

- Install the pinned, reviewed PhoneDriver release and verify its binary checksum/signature before execution.
- Install Android Platform Tools (ADB); use USB debugging initially.
- Enroll only the user's explicitly authorized Android device; verify the device serial before every session.
- Keep ADB authorized-device list minimal. Do not expose ADB over an unauthenticated TCP listener.
- Run `phonedriver doctor` and `phonedriver devices`; start with read-only snapshots and screenshots.
- Add the PhoneDriver MCP server to a dedicated local agent profile only after the AEGENTIX adapter enforces policy.

### iPhone / iOS

- A physical iPhone requires a Mac with Xcode and an Apple Development signing identity for the documented XCTest path; newer iOS versions may use CoreDevice.
- A Windows-only ROG Ally X is not sufficient for the documented physical-iPhone setup. Use a separately managed Mac as a trusted iOS device host, connected to AEGENTIX through an authenticated, encrypted, narrowly scoped channel.
- Do not expose the Mac's general shell or Xcode control surface to remote agents. The Mac-side service should accept only typed, authenticated mobile operations.
- Enroll and test the iPhone separately. Face ID/passcode unlock remains a human action; do not attempt to bypass it.

## 6. Proposed AEGENTIX adapter contract

The adapter should expose a small stable contract, independent of PhoneDriver's internal CLI/MCP details:

- `list_devices()` — enrolled devices and health, no sensitive screen data.
- `get_snapshot(device_id, scope)` — structured screen text with sensitive-field redaction.
- `get_screenshot(device_id, approval)` — on-demand image, privacy-gated and non-persistent by default.
- `perform_action(device_id, action, target, args, approval)` — typed action only; validate target, scope, expiry, and policy before dispatch.
- `cancel_session(device_id, reason)` — revoke lease and stop pending work.
- `get_session_status(device_id)` — active actor, granted scopes, expiry, and last result.

Every call must carry an authenticated AEGENTIX actor, device ID, correlation ID, least-privilege scope, and deadline. Reject unknown actions, unknown devices, expired approvals, stale sessions, and ambiguous targets. Return structured outcomes; never report success unless PhoneDriver confirms it.

## 7. Audit event model

Emit AEGENTIX audit events for enrollment, connection, snapshot access, screenshot access, action requested, action approved/denied, action dispatched, action result, session expiry, cancellation, and device removal.

Record: timestamp, actor/agent ID, device ID (pseudonymous where appropriate), session ID, correlation ID, action category, target role/label hash (not raw sensitive text), policy result, approval ID, driver result, and duration. Never log tokens, secrets, clipboard payloads, passwords, MFA codes, or raw screen contents.

## 8. AGPL-3.0 and distribution

The reviewed PhoneDriver README identifies the project as AGPL-3.0-only and describes a network-source offer requirement for modified versions used remotely over a network. Before bundling, modifying, distributing, or offering a combined PhoneDriver-based service, perform a license review covering the exact fork commit, notices, copied code, binary components, and dependency licenses. Preserve upstream attribution and notices. If AEGENTIX modifies and offers a covered version for remote network interaction, provide the corresponding source as required by AGPL-3.0 section 13. Obtain legal review for the intended deployment and commercial model; this document is an engineering note, not legal advice.

## 9. Delivery phases and acceptance criteria

**Phase 0 — source and supply-chain review**
- Pin the exact fork commit and compare it with upstream.
- Review Cargo workspace, build scripts, binary download/cache behavior, dependency notices, release provenance, and tests.
- Record license and checksum/SBOM evidence.

**Phase 1 — Android read-only proof**
- Windows host can run doctor/devices/snapshot/screenshot against one enrolled test device.
- No tap/type/clipboard/shell tool exposed to agents.
- Device disconnect, stale reference, timeout, and daemon restart fail safely.
- No screenshots or screen text written to persistent logs.

**Phase 2 — gated interaction**
- Add one low-risk allowlisted interaction (for example, opening a non-sensitive Settings page).
- Demonstrate AEGENTIX authorization, explicit approval, audit correlation, cancellation, and replay protection.
- Demonstrate payment/message/delete/install/settings-sensitive actions are denied without fresh human approval.

**Phase 3 — iOS host**
- Bring up the isolated Mac-side service and enroll one test iPhone.
- Verify platform-specific limits and reconnect behavior.
- Keep iOS actions behind the same AEGENTIX policy contract.

**Phase 4 — agent orchestration**
- Permit selected agents to request bounded tasks through the AEGENTIX adapter.
- Require task plans, per-action policy checks, execution limits, and final human-visible reports.

No phase is considered complete from documentation alone. Deployment, live device access, and successful tests must be independently verified on the user's hardware.

## 10. Current review findings

- The fork's `README.md` describes 17 MCP tools and a local daemon architecture.
- Android uses ADB plus an on-device helper; iOS uses CoreDevice on supported versions and XCTest runner paths for older iOS/simulator configurations.
- Physical iPhone operation requires a Mac with Xcode and a signing identity.
- PhoneDriver's own payment/delete guard is label-driven and has documented limitations; AEGENTIX must enforce an independent policy gate.
- The reviewed README states no telemetry and local device communication after the initial binary download; verify this claim against the pinned source and build before production use.
- This is an architecture integration record only. No PhoneDriver binary has been installed, no device has been connected, and no mobile action has been executed.
