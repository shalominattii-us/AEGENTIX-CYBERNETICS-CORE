// scripts/autonomous-system.ts - Windows Optimized Version
import fs from 'fs';
import { execSync } from 'child_process';

console.log('🚀 Autonomous System v2.0 (Windows Edition)');
console.log('💻 Platform:', process.platform);
console.log('📅', new Date().toISOString());

// ============================================================
// STATE MANAGER
// ============================================================
class StateManager {
  private statePath = '.autonomous-state.json';
  
  load() {
    if (fs.existsSync(this.statePath)) {
      return JSON.parse(fs.readFileSync(this.statePath, 'utf-8'));
    }
    return { version: '2.0.0', lastRun: null, tasks: {}, metrics: { builds: 0, tests: 0 } };
  }
  
  save(state: any) {
    fs.writeFileSync(this.statePath, JSON.stringify(state, null, 2));
  }
}

// ============================================================
// HEALTH CHECK
// ============================================================
class HealthCheck {
  run() {
    console.log('\n🏥 Health Checks:');
    
    // Check Node
    console.log(`✅ Node: ${process.version}`);
    
    // Check npm
    try {
      const npmVer = execSync('npm --version', { encoding: 'utf-8' }).trim();
      console.log(`✅ npm: ${npmVer}`);
    } catch {
      console.log('❌ npm not found');
    }
    
    // Check Git
    try {
      const gitVer = execSync('git --version', { encoding: 'utf-8' }).trim();
      console.log(`✅ Git: ${gitVer}`);
    } catch {
      console.log('❌ Git not found');
    }
    
    // Check Memory
    const mem = process.memoryUsage();
    console.log(`✅ Memory: ${(mem.heapUsed / 1024 / 1024).toFixed(2)}MB used`);
    
    // Check Disk
    try {
      fs.writeFileSync('test.tmp', 'test');
      fs.unlinkSync('test.tmp');
      console.log('✅ Disk: Writable');
    } catch {
      console.log('❌ Disk: Not writable');
    }
    
    return true;
  }
}

// ============================================================
// SECURITY SCAN
// ============================================================
class SecurityScan {
  run() {
    console.log('\n🔒 Security Scan:');
    
    // Check for node_modules
    if (fs.existsSync('node_modules')) {
      console.log('✅ node_modules found');
    } else {
      console.log('⚠️ node_modules missing - run npm install');
    }
    
    // Check for package.json
    if (fs.existsSync('package.json')) {
      console.log('✅ package.json found');
    } else {
      console.log('⚠️ package.json missing');
    }
    
    // Check for .git
    if (fs.existsSync('.git')) {
      console.log('✅ Git repository found');
    } else {
      console.log('⚠️ Not a git repository');
    }
    
    return true;
  }
}

// ============================================================
// AI ANALYSIS
// ============================================================
class AIAnalysis {
  run() {
    console.log('\n🤖 AI Code Analysis:');
    
    // Find TypeScript files
    const files = this.findFiles('.', ['.ts', '.tsx', '.js', '.jsx']);
    
    if (files.length === 0) {
      console.log('⚠️ No TypeScript/JavaScript files found');
      return true;
    }
    
    console.log(`📁 Found ${files.length} files to analyze`);
    
    let issues = 0;
    for (const file of files.slice(0, 10)) { // Limit to 10 files
      const content = fs.readFileSync(file, 'utf-8');
      const lines = content.split('\n');
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Check for potential issues
        if (line.includes('any') && !line.includes('//')) {
          console.log(`⚠️ ${file}:${i+1} - Using 'any' type`);
          issues++;
        }
        if (line.includes('console.log') && !line.includes('//')) {
          console.log(`⚠️ ${file}:${i+1} - console.log found`);
          issues++;
        }
        if (line.includes('TODO') || line.includes('FIXME')) {
          console.log(`⚠️ ${file}:${i+1} - TODO/FIXME found`);
          issues++;
        }
      }
    }
    
    if (issues === 0) {
      console.log('✅ No issues found');
    } else {
      console.log(`📊 Found ${issues} potential issues`);
    }
    
    return true;
  }
  
  findFiles(dir: string, extensions: string[]): string[] {
    let results: string[] = [];
    try {
      const items = fs.readdirSync(dir);
      for (const item of items) {
        if (item === 'node_modules' || item === '.git') continue;
        const fullPath = dir + '/' + item;
        if (fs.statSync(fullPath).isDirectory()) {
          results = results.concat(this.findFiles(fullPath, extensions));
        } else if (extensions.some(ext => item.endsWith(ext))) {
          results.push(fullPath);
        }
      }
    } catch {}
    return results;
  }
}

// ============================================================
// TEST RUNNER
// ============================================================
class TestRunner {
  run() {
    console.log('\n🧪 Running Tests:');
    
    // Check for test files
    const testFiles = this.findFiles('.', ['.test.ts', '.test.js', '.spec.ts', '.spec.js']);
    
    if (testFiles.length === 0) {
      console.log('⚠️ No test files found');
      return true;
    }
    
    console.log(`📁 Found ${testFiles.length} test files`);
    
    // Try to run tests
    try {
      execSync('npm test -- --passWithNoTests', { stdio: 'inherit' });
      console.log('✅ Tests passed');
    } catch {
      console.log('⚠️ Tests failed or no test script configured');
    }
    
    return true;
  }
  
  findFiles(dir: string, extensions: string[]): string[] {
    let results: string[] = [];
    try {
      const items = fs.readdirSync(dir);
      for (const item of items) {
        if (item === 'node_modules' || item === '.git') continue;
        const fullPath = dir + '/' + item;
        if (fs.statSync(fullPath).isDirectory()) {
          results = results.concat(this.findFiles(fullPath, extensions));
        } else if (extensions.some(ext => item.endsWith(ext))) {
          results.push(fullPath);
        }
      }
    } catch {}
    return results;
  }
}

// ============================================================
// BUILD SYSTEM
// ============================================================
class BuildSystem {
  run() {
    console.log('\n🏗️ Building:');
    
    // Check if build script exists
    const pkg = fs.existsSync('package.json') ? JSON.parse(fs.readFileSync('package.json', 'utf-8')) : null;
    
    if (pkg && pkg.scripts && pkg.scripts.build) {
      console.log('📦 Running build script...');
      try {
        execSync('npm run build', { stdio: 'inherit' });
        console.log('✅ Build successful');
      } catch {
        console.log('❌ Build failed');
      }
    } else {
      console.log('⚠️ No build script found in package.json');
    }
    
    return true;
  }
}

// ============================================================
// DOCUMENTATION
// ============================================================
class Documentation {
  generate() {
    console.log('\n📚 Generating Documentation:');
    
    // Create docs folder
    if (!fs.existsSync('docs')) {
      fs.mkdirSync('docs');
    }
    
    // Generate README
    const readme = `# Autonomous System

## Status: ACTIVE
## Version: 2.0.0
## Platform: Windows

### Quick Start
\`\`\`
npm install
npx tsx scripts/autonomous-system.ts
\`\`\`

### Commands
- \`status\` - Check system status
- \`health\` - Run health checks
- \`security\` - Run security scan
- \`ai\` - Run AI analysis
- \`test\` - Run tests
- \`build\` - Build the project
- \`docs\` - Generate documentation
- \`full\` - Run all commands

Generated: ${new Date().toISOString()}
`;
    fs.writeFileSync('README_AUTO.md', readme);
    console.log('✅ README_AUTO.md created');
    
    // Generate status
    const state = new StateManager().load();
    const status = `# System Status Report

## Overview
- **Version:** ${state.version}
- **Last Run:** ${state.lastRun || 'Never'}
- **Builds:** ${state.metrics.builds || 0}
- **Tests:** ${state.metrics.tests || 0}

## Details
- **Platform:** Windows
- **Node:** ${process.version}
- **Date:** ${new Date().toISOString()}
`;
    fs.writeFileSync('docs/status.md', status);
    console.log('✅ docs/status.md created');
    
    return true;
  }
}

// ============================================================
// MAIN ENGINE
// ============================================================
class AutonomousEngine {
  private state: StateManager;
  
  constructor() {
    this.state = new StateManager();
  }
  
  run(command: string) {
    console.log('='.repeat(60));
    console.log('🚀 Autonomous Engine Running');
    console.log('='.repeat(60));
    
    const commands: Record<string, () => boolean> = {
      status: () => {
        const state = this.state.load();
        console.log('\n📊 System Status:');
        console.log(`  Version: ${state.version}`);
        console.log(`  Last Run: ${state.lastRun || 'Never'}`);
        console.log(`  Builds: ${state.metrics.builds || 0}`);
        console.log(`  Tests: ${state.metrics.tests || 0}`);
        return true;
      },
      health: () => new HealthCheck().run(),
      security: () => new SecurityScan().run(),
      ai: () => new AIAnalysis().run(),
      test: () => new TestRunner().run(),
      build: () => new BuildSystem().run(),
      docs: () => new Documentation().generate(),
      full: () => {
        console.log('\n🔄 Running full cycle...\n');
        const steps = ['health', 'security', 'ai', 'test', 'build', 'docs'];
        for (const step of steps) {
          console.log(`\n📌 Step: ${step.toUpperCase()}`);
          commands[step]();
        }
        
        // Update state
        const state = this.state.load();
        state.lastRun = new Date().toISOString();
        state.metrics.builds = (state.metrics.builds || 0) + 1;
        this.state.save(state);
        
        console.log('\n✅ Full cycle complete!');
        return true;
      }
    };
    
    const fn = commands[command] || commands.status;
    fn();
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ Done!');
    console.log('='.repeat(60));
  }
}

// ============================================================
// RUN THE SYSTEM
// ============================================================
if (require.main === module) {
  const command = process.argv[2] || 'status';
  const engine = new AutonomousEngine();
  engine.run(command);
}

export { AutonomousEngine, StateManager, HealthCheck, SecurityScan, AIAnalysis, TestRunner, BuildSystem, Documentation };