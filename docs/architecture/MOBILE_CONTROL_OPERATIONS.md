# AEGENTIX Mobile Control — Operations and Deployment Runbook

**Status:** operational plan; no external service has been connected or deployed by this document  
**Architecture:** [MOBILE_DEVICE_CONTROL.md](./MOBILE_DEVICE_CONTROL.md)  
**PhoneDriver fork:** https://github.com/shalominattii-us/phonedriver

## 1. Roles and authority

AEGENTIX remains the system of record and policy authority. Supporting tools are replaceable operators, not independent authorities.

| System | Intended role | Must not do |
|---|---|---|
| AEGENTIX Gateway / CyberCore | Identity, policy, approvals, task routing, audit | Delegate policy decisions to external IDE agents |
| PhoneDriver | Local Android/iOS transport and UI automation | Bypass AEGENTIX authorization |
| Google Antigravity | Human-supervised coding, repository inspection, implementation and local debugging | Receive production secrets or independently approve deployment |
| Kilo Code | Coding-agent assistance, tests, code review and bounded implementation tasks | Execute production device actions or deploy without an approved pipeline |
| Cloudflare | DNS, TLS, Access, Tunnel, Workers/edge API, telemetry and deployment controls as applicable | Expose ADB, raw device sockets, unrestricted MCP stdio, or local shell |
| GitHub | Versioned source, pull requests, CI and release provenance | Store secrets in source or commit unreviewed generated binaries |

## 2. Target topology

```
Authorized operator / approved AEGENTIX agent
                    |
          Cloudflare Access (optional)
          TLS + identity + rate limits
                    |
       AEGENTIX public/edge API (Worker)
       - validates signed short-lived requests
       - forwards typed, scoped task envelopes
       - no device credentials or raw screen archive
                    |
        outbound authenticated connector
        (Cloudflare Tunnel or equivalent)
                    |
       Local AEGENTIX gateway on Windows
       - identity and policy enforcement
       - human approval and session lease
       - audit and emergency stop
                    |
          PhoneDriver local MCP/daemon
                    |
          enrolled Android device

iPhone path: isolated Mac host + Xcode/CoreDevice/XCTest
             -> authenticated typed connector
             -> same AEGENTIX policy and audit plane
```

A Cloudflare Worker is stateless edge/control-plane compute, not the place to run ADB, PhoneDriver's persistent daemon, Xcode, or a device session. Keep device transport on the trusted local host. Prefer outbound-only connectivity from the local host; do not open inbound router ports.

Cloudflare Tunnel/Access are optional deployment choices and must be configured only after reviewing the current account, domain, policies, and connector capabilities. Do not assume a Worker can directly reach a private local service without a deliberate, authenticated connectivity design.

## 3. Tooling workflow

### Antigravity — development workspace
1. Open the AEGENTIX core repository and PhoneDriver fork as separate workspaces.
2. Review the current branch, working tree and integration architecture before editing.
3. Implement in a feature branch; preserve upstream PhoneDriver as a separately versioned dependency.
4. Use local test fixtures and mocked device responses until a physical test device is deliberately enrolled.
5. Require a human review of diffs, dependency changes and security-sensitive code.

### Kilo Code — bounded coding agent
1. Assign small, explicit issues (adapter interface, schema validation, tests, documentation).
2. Grant repository-only access; do not provide Cloudflare API tokens, Apple signing keys, device unlock secrets or production credentials to prompts.
3. Require tests, changed-file summaries and explicit security review.
4. Keep shell, deployment, device control and production write actions disabled unless separately authorized by the operator.

### GitHub — source and release control
1. Pin PhoneDriver to a reviewed commit SHA; do not track a moving branch in production.
2. Use feature branches and pull requests for all code changes.
3. Run lint, unit tests, dependency/license checks, secret scanning and an SBOM build.
4. Require a human approval before merge and release.
5. Keep deployment credentials in the platform's secret store, never in repository files, issue comments or logs.

### Cloudflare — edge and delivery
1. Inventory the existing account, zones, Workers, tunnels, Access applications, DNS records, secrets and environments before changing anything.
2. Identify the existing AEGENTIX gateway hostname and its current origin. Do not create duplicate DNS records or overwrite existing routes.
3. Start with a non-production Worker and staging hostname.
4. Protect operator endpoints with Cloudflare Access and strong identity; apply rate limits and request-size limits.
5. Require signed, short-lived, replay-resistant task envelopes between edge and local gateway.
6. Store secrets in Worker secrets or an approved secret manager. Rotate any token exposed to build logs or source.
7. Publish only typed AEGENTIX API routes. Never proxy arbitrary URLs, shell commands, raw MCP calls, ADB ports, screenshots or clipboard content by default.
8. Test denial paths, expired signatures, replay, revoked users, origin outage and emergency-stop behavior before production promotion.
9. Promote via reviewed release and rollback plan; monitor errors and audit events.

## 4. Deployment sequence

**Stage A — inventory (read-only)**
- Confirm repository branch/commit and PhoneDriver pinned version.
- Inspect Windows host prerequisites and installed versions.
- Inventory Cloudflare resources and existing gateway routes without mutation.
- Determine whether Antigravity and Kilo are installed locally and which workspace/repository they can access.
- Record missing permissions and credentials as blockers; never infer that a connector is active from a product name.

**Stage B — Android local proof**
- Install reviewed PhoneDriver release and Android Platform Tools on Windows.
- Enroll one user-authorized Android test device.
- Run diagnostics and read-only device listing/snapshot.
- Verify AEGENTIX adapter denies all writes by default.
- Capture test output without persistent screen contents or secrets.

**Stage C — guarded Android interaction**
- Add one low-risk, allowlisted UI operation.
- Verify actor identity, per-device session lease, explicit approval, audit correlation, expiry, cancellation and fail-closed behavior.
- Confirm payment, message/post, delete, install, credential and account/security-setting actions are denied without fresh, explicit approval.

**Stage D — Cloudflare staging**
- Only after account/resource inventory and local gateway hardening, provision a staging edge route.
- Validate Access identity, signed envelopes, replay prevention, rate limits, origin isolation and rollback.
- Keep local PhoneDriver unreachable from the public internet.

**Stage E — iOS host**
- Provision and harden a separate Mac host with Xcode and required signing setup.
- Expose only the same typed AEGENTIX adapter contract; do not expose general Mac shell or Xcode tools to remote agents.
- Test with one enrolled iPhone; keep unlock and biometric authentication human-operated.

**Stage F — production promotion**
- Require passing CI, security review, license review, staging test evidence and operator approval.
- Deploy versioned artifacts with rollback.
- Confirm health and audit telemetry after promotion.

## 5. Required configuration inventory

Before any Cloudflare mutation, collect and confirm:
- Cloudflare account and zone identifiers (do not paste API tokens into chat).
- Existing AEGENTIX hostname, DNS target, Worker names, routes and environments.
- Existing Tunnel name/connector status and Access applications/policies.
- Current gateway origin address/port and authentication method.
- Whether a staging subdomain already exists.
- Desired operator identity provider and access groups.

Before local deployment, confirm:
- Windows version, PowerShell version, CPU architecture and available disk.
- ADB version and authorized device serial.
- PhoneDriver release/commit and checksum.
- Whether the PhoneDriver daemon is already running.
- Existing AEGENTIX gateway process/port to avoid collisions.
- Backup and rollback method.

Never request or record API tokens, private keys, passwords, Apple signing private keys, recovery phrases, MFA codes, or device passcodes in this document.

## 6. Stop conditions

Stop and request operator intervention if:
- Cloudflare account/zone ownership or existing routes cannot be established.
- A change would overwrite a production DNS record, Worker route, Access policy or Tunnel.
- Local gateway authentication or audit is unavailable.
- A device identity changes or a device is unexpectedly re-enrolled.
- A requested action has external, financial, destructive, account-security or privacy impact and lacks fresh approval.
- Dependency provenance, license compatibility or binary integrity is uncertain.
- A test requires exposing raw ADB, shell, MCP or device-control ports to the public internet.

## 7. Current execution status

This runbook records the intended orchestration. It does not assert that Cloudflare, Antigravity or Kilo is connected to this ChatGPT session, installed on the Windows host, or authorized to access the repositories. It does not claim a Worker, Tunnel, DNS record, local package, PhoneDriver daemon, device session or production deployment has been created.

The next executable step is a read-only inventory in the user's Antigravity/Kilo/Cloudflare environments, followed by a local Android read-only proof. Only verified account access and user-controlled host execution can establish those states.
