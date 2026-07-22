# Human–AI Submission Collaboration

## Purpose
Create a smooth, approval-centered workflow for proposals, patent-candidate packages, and organizational correspondence without allowing unauthorized external actions.

## Required flow
1. Resolve the intended organization from the verified organization directory.
2. Apply the verified submission email, CC recipients, address, jurisdiction, and sector metadata.
3. Generate or retrieve the current engineering program and export manifest.
4. Render one current PDF or DOCX package for every required supporting artifact.
5. Assemble one complete submission package containing:
   - addressed proposal correspondence;
   - subject and body appropriate to the receiving organization;
   - proposal draft;
   - architecture and subsystem documentation;
   - interfaces, risks, verification, and simulation plans;
   - manufacturing and documentation plans;
   - compliance material;
   - patent-candidate material when relevant;
   - immutable manifest and content hashes.
6. Create a human review item and emit `human.review.required` through Cybercore.
7. Present one-click approve, deny, and request-changes actions.
8. Require an `AEGENTIX-AUTH-*` token for every approval decision.
9. Only after package approval, create a Gmail draft with the verified recipients and every supporting document attached.
10. Keep `sendBlocked=true` and `externalActionBlocked=true` after draft creation. Sending, filing, bidding, financial commitment, or external representation requires a separate explicit authorization.

## Review experience
- Default view: `GET /api/reviews/inbox`.
- Review actions:
  - `POST /api/reviews/{reviewId}/approve`
  - `POST /api/reviews/{reviewId}/deny`
  - `POST /api/reviews/{reviewId}/request-changes`
- Show title, summary, recipient, attachment count, hashes, required reviewer role, due date, and the exact action being authorized.
- Never reuse approval for a changed artifact or package hash.

## Complete package endpoints
- `POST /api/organizations`
- `GET /api/organizations`
- `POST /api/engineering-programs/{programId}/complete-package`
- `GET /api/complete-packages/{packageId}`
- `POST /api/complete-packages/{packageId}/gmail-draft`

## Notification events
- `human.review.required`
- `human.review.decided`
- `engineering.export_manifest.created`
- `correspondence.gmail_draft.created`

Route these events through Cybercore to the configured notification surfaces. Notifications should include direct review identifiers and the requested reviewer role, but never authorization tokens or confidential attachment contents.

## Safety invariant
Every stage is individually approval-gated. Package approval authorizes only Gmail draft creation. Gmail draft creation does not authorize sending. No proposal submission, patent filing, bid, financial commitment, or external representation occurs without explicit user authorization for that exact action.
