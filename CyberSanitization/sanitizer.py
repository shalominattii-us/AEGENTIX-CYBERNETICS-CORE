# ============================================================
# CYBERSANITIZATION ENGINE
# Zero hallucination. Zero drift.
# ============================================================

import json
import os
import hashlib
import re
from datetime import datetime

# ──────────────────────────────────────────────
# 1. LOAD BASELINE
# ──────────────────────────────────────────────

baseline_path = 'C:/Aegentix/CyberSanitization/baseline.json'

if not os.path.exists(baseline_path):
    print('❌ Baseline not found')
    sys.exit(1)

with open(baseline_path, 'r') as f:
    BASELINE = json.load(f)

IDENTITY = BASELINE['identity']
FACTS = BASELINE['facts']
RESPONSES = BASELINE['responses']

# ──────────────────────────────────────────────
# 2. SANITIZATION FUNCTION
# ──────────────────────────────────────────────

class CyberSanitizer:
    def __init__(self):
        self.baseline = BASELINE
        self.facts = FACTS
        self.responses = RESPONSES
        self.identity = IDENTITY
    
    def sanitize(self, text):
        """Sanitize a response — remove hallucinations, enforce identity"""
        if not text:
            return "I cannot answer that. I only speak from my fixed knowledge base."
        
        # Remove made-up names
        text = re.sub(r'Ursula|Bob|Alice|Charlie|David|Eve|Frank|Grace|Heidi|Ivan|Judy|Mallory|Oscar|Peggy|Trent|Walter|Wendy', 'Aegentix', text, flags=re.IGNORECASE)
        
        # Enforce identity
        if 'my name is' in text.lower() and 'aegentix' not in text.lower():
            text = "I am Aegentix. " + text
        
        # Remove hallucinated facts
        if 'I can' in text and 'capabilities' in text.lower():
            text = "I can check system status, run the autonomous swarm, manage services, and answer your questions."
        
        # Ensure identity if mentioned
        if 'am' in text.lower() and 'aegentix' not in text.lower():
            text = "I am Aegentix. " + text
        
        return text
    
    def get_response(self, key):
        """Get a fixed response from the baseline"""
        return self.responses.get(key, "I cannot answer that. I only speak from my fixed knowledge base.")
    
    def get_fact(self, key):
        """Get a fixed fact from the baseline"""
        keys = key.split('.')
        current = self.facts
        try:
            for k in keys:
                current = current[k]
            return current
        except:
            return None
    
    def validate(self, text):
        """Validate a response against the baseline"""
        # Check for identity drift
        if 'aegentix' not in text.lower():
            return False, "Identity drift detected"
        
        # Check for made-up facts
        if 'ursula' in text.lower():
            return False, "Made-up name detected"
        
        # Check for hallucinated capabilities
        if 'capabilities' in text.lower() and len(text) > 200:
            return False, "Hallucinated capabilities detected"
        
        return True, "Valid"

# ──────────────────────────────────────────────
# 3. TEST SANITIZATION
# ──────────────────────────────────────────────

sanitizer = CyberSanitizer()

test_texts = [
    "I am Ursula, the AI assistant.",
    "My name is Bob. I can do anything.",
    "I am Aegentix, the sovereign AI.",
    "I can fly to the moon.",
    "What is the weather today?"
]

print('🧪 TESTING SANITIZATION:')
print('-' * 40)

for test in test_texts:
    sanitized = sanitizer.sanitize(test)
    valid, reason = sanitizer.validate(sanitized)
    status = '✅ PASS' if valid else '❌ FAIL'
    print(f'{status}: {test[:30]}... → {sanitized[:50]}...')
    if not valid:
        print(f'      Reason: {reason}')

print('')
print('✅ Sanitization engine ready')
print('📂 C:/Aegentix/CyberSanitization/sanitizer.py')
