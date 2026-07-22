# AEGENTIX Government Operations Spine

Initial vertical slice connecting public opportunity intake to Treasury Labs parsing, build-spec generation, Infinite Brain OS task planning, capability matching, and approval-gated external actions.

## Implemented flow

1. Normalize an authoritative public opportunity into `PublicOpportunity`.
2. Parse source text into traceable Treasury Labs requirements.
3. Generate a draft build specification.
4. Create an Infinite Brain OS dependency graph across OpenClaw, Nemotron, Docker, Hermes, and Manus.
5. Match extracted requirements against an AEGENTIX capability registry.
6. Block bid submission, patent filing, financial commitments, and external representations unless an explicit authorization token is supplied.

## Run locally

```bash
cd government-ops-spine
npm install
npm test
```

## Next implementation priorities

- Persist opportunities, amendments, provenance, analyses, and build state in PostgreSQL.
- Add adapters for the daily opportunity intake payload.
- Replace heuristic parsing with a versioned model-assisted parser plus schema validation.
- Index AEGENTIX repositories, deployments, tests, CAD, and documentation into the capability registry.
- Add patent-workbench and proposal-factory artifact schemas behind human approval gates.

## Safety boundary

This package may generate internal drafts, specifications, simulations, and execution plans. It must not submit bids, grants, patent filings, financial commitments, or external representations without explicit human authorization.
