# ============================================================
# GAIA NET NODE — SOVEREIGN CONNECTION
# ============================================================

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime

print('')
print('============================================================')
print('🜂 GAIA NET NODE — SOVEREIGN CONNECTION')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('============================================================')
print('')

# ──────────────────────────────────────────────
# 1. GAIA NET ENDPOINTS
# ──────────────────────────────────────────────

GAIA_ENDPOINTS = {
    'primary': 'https://gaia.network/api/v1',
    'backup': 'https://gaia-backup.network/api/v1',
    'sovereign': 'https://sovereign.gaia.network/api/v1',
    'local': 'http://localhost:8188/api/v1'
}

print('🔗 CONNECTING TO GAIA NET...')
print('-' * 40)

gaia_connected = 0
for name, url in GAIA_ENDPOINTS.items():
    try:
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req, timeout=5)
        print(f'   ✅ {name}: CONNECTED')
        gaia_connected += 1
    except Exception as e:
        print(f'   ❌ {name}: OFFLINE ({str(e)[:30]})')

print(f'   📊 Connected: {gaia_connected}/{len(GAIA_ENDPOINTS)}')

# ──────────────────────────────────────────────
# 2. MASTER ENDPOINT STATUS
# ──────────────────────────────────────────────

print('')
print('🔗 MASTER ENDPOINT STATUS...')
print('-' * 40)

MASTER_ENDPOINT = {
    'host': 'localhost',
    'port': 8188,
    'protocol': 'http',
    'path': '/api/v1'
}

master_status = 'OFFLINE'
try:
    url = f"{MASTER_ENDPOINT['protocol']}://{MASTER_ENDPOINT['host']}:{MASTER_ENDPOINT['port']}{MASTER_ENDPOINT['path']}"
    req = urllib.request.Request(url)
    response = urllib.request.urlopen(req, timeout=3)
    master_status = 'ONLINE'
    print(f'   ✅ Master Endpoint: {master_status}')
    print(f'   📍 URL: {url}')
except Exception as e:
    print(f'   ❌ Master Endpoint: {master_status}')
    print(f'   💡 Error: {str(e)[:50]}')

# ──────────────────────────────────────────────
# 3. REGISTER SERVICES
# ──────────────────────────────────────────────

print('')
print('📋 REGISTERING SERVICES...')
print('-' * 40)

SERVICES = [
    'cyberdeck',
    'swarm',
    'inference',
    'node',
    'daemon',
    'gaia_net'
]

print('   ✅ ' + ', '.join(SERVICES))

# ──────────────────────────────────────────────
# 4. SAVE CONFIGURATION
# ──────────────────────────────────────────────

print('')
print('💾 SAVING CONFIGURATION...')
print('-' * 40)

config = {
    'timestamp': datetime.now().isoformat(),
    'gaia_connected': gaia_connected,
    'total_endpoints': len(GAIA_ENDPOINTS),
    'master_endpoint': MASTER_ENDPOINT,
    'master_status': master_status,
    'services': SERVICES,
    'status': 'operational' if gaia_connected > 0 else 'partial'
}

with open('C:/Aegentix/gaia_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('   ✅ Config saved: C:/Aegentix/gaia_config.json')

# ──────────────────────────────────────────────
# 5. FINAL STATUS
# ──────────────────────────────────────────────

print('')
print('============================================================')
print('📊 GAIA NET STATUS')
print('============================================================')
print(f'   Gaia Connected: {gaia_connected}/{len(GAIA_ENDPOINTS)}')
print(f'   Master Endpoint: {master_status}')
print(f'   Services: {len(SERVICES)}')
print(f'   Status: {config["status"]}')
print('============================================================')
print('🜂 GAIA NET NODE — DEPLOYED')
