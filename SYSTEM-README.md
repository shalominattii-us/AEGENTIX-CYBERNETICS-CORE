# AEGENTIX CYBERNETICS CORE - Opportunity Processing System

## Overview
This system organizes government opportunities by type and classification, processes them through the government-ops-spine pipeline, and uses agents for continuous automation.

## Architecture

### Opportunity Types (Government)
- RFI, RFP, RFQ, IFB, BAA, CSO, OTA, SBIR, STTR, GRANT
- COOPERATIVE_AGREEMENT, PRIZE, CHALLENGE, SOURCES_SOUGHT, FORECAST
- LICENSING, PARTNERSHIP, SUBCONTRACT, OTHER

### Execution Zones (Infrastructure)
- KERNEL, TREASURY, AI, SECURITY, XR, DATA, CLOUD, ORBITAL, FACTORY, SOVEREIGN

### Processing Flow
1. **Ingestion**: Opportunities added to `opportunities/{TYPE}/`
2. **Parsing**: government-ops-spine parses opportunities
3. **Analysis**: Treasury analysis extracts requirements
4. **Specification**: Build specifications generated
5. **Planning**: Brain plans created with tasks per zone
6. **Execution**: Agents work on tasks continuously

## Directory Structure
```
AEGENTIX-CYBERNETICS-CORE/
├── opportunities/          # Opportunity intake by type
│   ├── RFI/, RFP/, etc.   # Organized by opportunity type
├── projects/              # Project implementations by zone
│   ├── KERNEL/, AI/, etc. # Organized by execution zone
├── government-ops-spine/  # Core processing engine
├── platform/              # Platform services
└── agents/               # Agent configurations
```

## Usage
1. Add opportunities to `opportunities/{TYPE}/` as JSON files
2. Run the processing pipeline
3. Agents will continuously process and generate outputs
4. Results go to `projects/{ZONE}/`
