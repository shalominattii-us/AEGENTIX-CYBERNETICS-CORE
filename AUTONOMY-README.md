# AEGENTIX Autonomy Setup

## Quick Start

### 1. Build the government-ops-spine
```bash
cd government-ops-spine
npm install
npm run build
```

### 2. Set Environment Variables
```bash
export EXECUTION_ZONES=KERNEL,TREASURY,AI,SECURITY,XR,DATA,CLOUD,ORBITAL,FACTORY,SOVEREIGN
export PROCESSING_MODE=continuous
export AGENTS_ENABLED=true
```

### 3. Start Continuous Processing
```bash
# In terminal 1: Start the government-ops-spine server
cd government-ops-spine
npm start

# In terminal 2: Start continuous processor
cd AEGENTIX-CYBERNETICS-CORE
npx ts-node processing/continuous-processor.ts
```

### 4. Add Opportunities
Add JSON files to `opportunities/{TYPE}/` directories.

Example opportunity format:
```json
{
  "schemaVersion": "1.0.0",
  "eventId": "opp-123",
  "externalId": "RFP-2024-001",
  "title": "Advanced AI System",
  "issuer": "Department of Defense",
  "jurisdiction": "US",
  "opportunityType": "RFP",
  "publicationDate": "2024-01-01T00:00:00Z",
  "deadline": "2024-12-31T00:00:00Z",
  "eligibility": ["US entities"],
  "requiredRegistrations": ["SAM"],
  "summary": "Advanced AI system for autonomous operations",
  "provenance": [
    {
      "system": "SAM.gov",
      "authority": "official",
      "url": "https://sam.gov/...",
      "retrievedAt": "2024-01-01T00:00:00Z"
    }
  ]
}
```

## System Status
- ✅ Opportunity folders organized by type
- ✅ Project folders organized by execution zone
- ✅ Government-ops-spine updated with dynamic zones
- ✅ Continuous processing system created
- ✅ Agent configurations defined
- ✅ Autonomy framework ready

## Next Steps
1. Add opportunities to process
2. Start the agents
3. Monitor results in `projects/`
4. Scale as needed
