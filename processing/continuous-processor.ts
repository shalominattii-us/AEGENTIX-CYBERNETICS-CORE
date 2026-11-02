# AEGENTIX Continuous Processing Script

```typescript
import { runInternalPipeline } from '../government-ops-spine/src/pipeline.js';
import { getExecutionZones } from '../government-ops-spine/src/zones.js';
import fs from 'fs';
import path from 'path';

const OPPORTUNITIES_DIR = './opportunities';
const PROJECTS_DIR = './projects';
const ZONES = getExecutionZones();

console.log('AEGENTIX Continuous Processing Starting...');
console.log(`Execution Zones: ${ZONES.join(', ')}`);

async function processOpportunity(filePath: string, type: string) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const opportunity = JSON.parse(content);
    
    // Set opportunity type from directory
    opportunity.opportunityType = type;
    
    // Run pipeline
    const result = runInternalPipeline(opportunity);
    
    // Determine primary zone
    const primaryZone = result.specification.executionZones[0] || ZONES[0];
    
    // Create project folder
    const projectDir = path.join(PROJECTS_DIR, primaryZone, opportunity.externalId);
    fs.mkdirSync(projectDir, { recursive: true });
    
    // Write outputs
    fs.writeFileSync(
      path.join(projectDir, 'analysis.json'),
      JSON.stringify(result.analysis, null, 2)
    );
    fs.writeFileSync(
      path.join(projectDir, 'specification.json'),
      JSON.stringify(result.specification, null, 2)
    );
    fs.writeFileSync(
      path.join(projectDir, 'plan.json'),
      JSON.stringify(result.plan, null, 2)
    );
    
    console.log(`Processed ${opportunity.externalId} -> ${primaryZone}/${opportunity.externalId}`);
    
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error);
  }
}

async function processAll() {
  const opportunityTypes = fs.readdirSync(OPPORTUNITIES_DIR)
    .filter(f => fs.statSync(path.join(OPPORTUNITIES_DIR, f)).isDirectory());
  
  for (const type of opportunityTypes) {
    const typeDir = path.join(OPPORTUNITIES_DIR, type);
    const files = fs.readdirSync(typeDir).filter(f => f.endsWith('.json'));
    
    for (const file of files) {
      const filePath = path.join(typeDir, file);
      await processOpportunity(filePath, type);
    }
  }
}

// Continuous processing loop
async function continuousProcess() {
  while (true) {
    try {
      await processAll();
      console.log('Processing cycle complete. Waiting 30s...');
      await new Promise(resolve => setTimeout(resolve, 30000));
    } catch (error) {
      console.error('Error in processing loop:', error);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  }
}

continuousProcess();
```
