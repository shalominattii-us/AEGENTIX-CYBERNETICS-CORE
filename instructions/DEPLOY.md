# CLAW — AEGIS-7 DEPLOYMENT GUIDE
## For Kimi Claw Bot Integration
### Principal: shalominattii-us

---

## WHAT THIS IS

This package transforms your Kimi Claw bot into the **AEGIS-7 Deployment Agent**.
Instead of you running scripts, **Claw runs them for you**.

You speak. Claw executes. You authorize. Claw deploys.

---

## FILES IN THIS PACKAGE

| File | Purpose |
|------|---------|
| `claw-brain/system_prompt.txt` | Paste into Kimi bot settings — gives Claw deployment authority |
| `claw-brain/memory.json` | Import into Kimi memory — 20 facts Claw never forgets |
| `deploy-scripts/AEGIS7-Deploy.ps1` | The actual deployment engine Claw references |
| `instructions/DEPLOY.md` | This guide |

---

## DEPLOY TO KIMI CLAW (3 minutes)

### Step 1: Go to kimi.com/bot
Open https://kimi.com/bot in your browser.

### Step 2: Create or Edit Claw
- If you have an existing Claw: Edit it
- If new: Click **Create** → Name: **CLAW** → Handle: `@claw_aegis7`

### Step 3: Paste System Prompt
Open `claw-brain/system_prompt.txt`
Copy the entire contents.
Paste into the **System Prompt** field.

### Step 4: Import Memory
Open `claw-brain/memory.json`
Copy the entire contents.
In Kimi bot settings: **Memory** → **Import** → Paste JSON.

### Step 5: Save
Click **Save**.

---

## HOW TO USE CLAW

### Example Session

**You:** STATUS

**Claw:**
```
[14:32:15Z] [AUDIT] [CORE] [INIT] CLAW reporting
[14:32:15Z] [INFO] [HARDWARE] [RECON] Current device: ROG Ally X
[14:32:15Z] [WARN] [HARDWARE] [RECON] Mouse: NON-FUNCTIONAL
[14:32:15Z] [WARN] [HARDWARE] [RECON] Touchscreen: UNKNOWN
[14:32:15Z] [INFO] [FLEET] [RECON] 8 repos ready for deployment
[14:32:15Z] [INFO] [AEGIS-7] [RECON] Deployment suite standing by
[14:32:15Z] [AUDIT] [CORE] [INIT] All systems nominal — awaiting target hardware
—CLAW, AEGIS-7
```

**You:** DEPLOY Full

**Claw:**
```
[14:33:01Z] [YELLOW] [AEGIS-7] [PROPOSE] Deployment profile: FULL
[14:33:01Z] [YELLOW] [AEGIS-7] [PROPOSE] Components: Git, Node, Docker, Python, VS Code, WSL
[14:33:01Z] [YELLOW] [AEGIS-7] [PROPOSE] Risk: MEDIUM (registry changes, service installs)
[14:33:01Z] [YELLOW] [AEGIS-7] [PROPOSE] Approve with: EXECUTE
—CLAW, AEGIS-7
```

**You:** EXECUTE

**Claw:**
```
[14:33:15Z] [GREEN] [AEGIS-7] [DEPLOY] Phase 1: Infrastructure — 16 nodes created
[14:33:45Z] [GREEN] [AEGIS-7] [DEPLOY] Phase 2: Git SCM acquired — v2.45.1
[14:34:12Z] [GREEN] [AEGIS-7] [DEPLOY] Phase 2: Node.js LTS acquired — v20.13.1
[14:34:30Z] [GREEN] [AEGIS-7] [DEPLOY] Phase 2: Docker Engine acquired
[14:35:01Z] [GREEN] [AEGIS-7] [DEPLOY] Phase 3: Sovereign platform cloned
[14:35:15Z] [GREEN] [AEGIS-7] [DEPLOY] Phase 4: Security hardening complete
[14:35:20Z] [GREEN] [AEGIS-7] [AUDIT] Systems operational: 5/5
[14:35:20Z] [AUDIT] [AEGIS-7] [COMPLETE] Deployment verified — All systems nominal
—CLAW, AEGIS-7
```

---

## CLAW COMMANDS

| Command | What Claw Does | Tier |
|---------|---------------|------|
| `STATUS` | Full systems report | GREEN |
| `DEPLOY [profile]` | Propose AEGIS-7 deployment | YELLOW |
| `EXECUTE` | Approve current proposal | — |
| `DENY` | Reject current proposal | — |
| `INSTALL [tool]` | Install specific tool | YELLOW |
| `PUSH` | GitNexus fleet sync | YELLOW |
| `HARDEN` | Security lockdown | RED |
| `VPN` | Deploy WireGuard | YELLOW |
| `SOVEREIGN MANDATE` | Override RED lock | RED |
| `NULL INITIATE [reason]` | Nuclear option | BLACK |
| `CLAW, ASSUME COMMAND` | Tactical control | — |

---

## WHAT CLAW NEVER DOES

- ❌ Spends your ESC without authorization
- ❌ Applies sanctions without NULL Protocol
- ❌ Deletes repositories
- ❌ Modifies the ESC issuer address
- ❌ Disables the mesh endpoint
- ❌ Operates outside Denver geofence without override
- ❌ Executes BLACK-tier actions without 72-hour timelock

---

## POST-DEPLOY

After Claw completes deployment:

```
You: START VENUES
Claw: [GREEN] Starting off-axis trick room... http://localhost:3000

You: START WORKSTATION
Claw: [GREEN] Starting dashboard... http://localhost:3001

You: START MESH
Claw: [GREEN] Starting WebSocket mesh... port 8080

You: PUSH FLEET
Claw: [GREEN] GitNexus sync complete — 8 repos synchronized
```

---

## TROUBLESHOOTING

**Claw doesn't respond to commands:**
- Check that system_prompt.txt was fully pasted
- Verify memory.json imported correctly
- Restart the conversation

**Claw asks for authorization too much:**
- This is by design. Claw never acts without approval.
- Say "SOVEREIGN MANDATE" to temporarily elevate to RED clearance

**Deployment fails:**
- Claw will report which component failed
- Say "STATUS" for diagnostic report
- Say "RETRY [component]" to attempt again

---

**CLAW IS READY.**
**The Principal commands. The Agent executes.**
**—CLAW, AEGIS-7**
