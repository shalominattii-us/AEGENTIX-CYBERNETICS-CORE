# Unified Sovereign Workspace — integration baseline

Hermes is the managed Bun/React/Hono operator shell for the apps preserved in
`AEGENTIX-CYBERNETICS-CORE/sources`. Preservation is not runtime integration.

## Verified in this revision

- Public email/password signup is disabled.
- Every Governor, Galaxy, Notebook and Jarvis procedure requires the configured
  owner user ID, not merely a signed-in account.
- Missing owner binding denies all console access. There is no first-user claim.
- Owner binding uses `HERMES_OWNER_USER_ID` in the deployment's root `.env`.
  Sign in through the identity gate to see your own verified user ID, then have
  the deployment administrator bind it. Never bind the smoke-test identity.
- Arbitrary request origins are no longer trusted automatically. Additional
  allowed origins must be explicitly listed in `AUTH_TRUSTED_ORIGINS`.
- Galaxy repo slugs are namespaced to avoid the `sovereign-os` repo/note collision.
- Concurrent Galaxy seeding in one process shares one promise.
- Galaxy smoke test: 88 nodes, 91 links, one seeded notebook.

## Consolidation inventory

`repository-inventory.json` records 82 preserved source directories. Twenty-seven
have runtime manifests at their root. Nested apps still need inspection. Every
entry is marked **unverified**, because manifest presence proves neither a build
nor a running service. No collected repo has been executed by the inventory pass.

Next integration gates:

1. Inspect nested manifests, dependencies, licenses, runtime requirements and
   secrets; distinguish apps from libraries, archives and deployment scripts.
2. Resolve duplicate capabilities; migrate UI surfaces into this managed shell.
3. Integrate needed service capabilities through typed adapters, explicit resource
   budgets and health checks. Do not launch all source repos blindly.
4. Verify each adapter and full workflows on the ROG; only then claim operational
   integration or produce the final unified distribution.

## Kilo Code

Include Kilo as a coding worker/provider adapter, not the identity authority or
the entire OS. Its local-provider support is documented at
https://kilo.ai/docs/automate/extending/local-models and
https://kilo.ai/docs/ai-providers/ollama.

Local inference is the default; external APIs require explicit opt-in. Kilo is
not installed or connected in this revision. Model switching does not by itself
provide repo compilation, credential custody or autonomous job execution.

## Credential custody boundary

The intended identity/credential subsystem serves the owner across mail,
logins and delegated tools. It is **not implemented yet**. Passwords, tokens and
private keys must not enter Galaxy bodies, shared memory, model prompts or source
control. A future implementation needs an encrypted local vault, scoped secret
references, rotation, recovery and auditable access—not agent-readable plaintext.

## Known limits

- Owner binding remains unset until the owner's identity is verified and bound.
- Google broker sign-in has not been exercised interactively in this sandbox.
- Neither Windows installation script has been executed on the ROG.
- This template uses a managed database; the local-only installation path is not
  complete. The bootstrap must not be described as fully independent yet.
- Governor/Jarvis remote-unit connectivity is unverified.
- Full app consolidation, CyberGenNet execution and credential management are
  subsequent work, not completed features of this commit.