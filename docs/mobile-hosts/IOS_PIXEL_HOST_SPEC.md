# AEGENTIX Mobile Hosts — iOS + Pixel

## Scope
Application-layer mobile hosts for AEGENTIX. The host runs above the native operating system and does not replace or weaken it.

## Security invariants
- No jailbreak/root.
- No protected system partition modification.
- No code-signing bypass.
- No Secure Enclave/Android Keystore bypass.
- No carrier/cellular provisioning changes.
- Native OS security remains authoritative.

## Node contract
Each device is an AEGENTIX node with:
1. Stable AEGENTIX node identity.
2. Authenticated connection to AEGENTIS CORE.
3. Guardian/policy decision before execution.
4. Event-first local journal.
5. Deterministic reconciliation after offline operation.
6. Explicit UNKNOWN state when continuity cannot be proven.

## iOS host
Use Swift/SwiftUI, App Intents, Shortcuts, BackgroundTasks, UserNotifications, ActivityKit, Keychain and standard HTTPS/WebSocket networking. Background execution is opportunistic and system-governed; the host must not assume continuous execution. Apple documents BGAppRefreshTask/BGProcessingTask and foreground/background App Intents for this model.

## Pixel host
Use Kotlin/Jetpack Compose, WorkManager, Android Intents/App Links, notifications, Android Keystore, BiometricPrompt and standard HTTPS/WebSocket networking. Foreground services are used only for workloads that qualify and with their required service type/permission declarations.

## Operational rule
Mobile hosts are execution/presence nodes, not independent authorities. A mobile node cannot grant itself permissions, fabricate continuity, or bypass Guardian decisions.
