# ============================================================
# LOCAL SOVEREIGN NETWORK
# ============================================================

import json
import os
import sys
import time
import socket
import urllib.request
import urllib.error
from datetime import datetime

print('')
print('============================================================')
print('🜂 LOCAL SOVEREIGN NETWORK')
print(f'📅 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('============================================================')
print('')

# ──────────────────────────────────────────────
# 1. LOCAL NETWORK SCAN
# ──────────────────────────────────────────────

print('🔍 SCANNING LOCAL NETWORK...')
print('-' * 40)

def scan_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

# Check key ports
ports = {
    'Master Endpoint': 8188,
    'Node': 8545,
    'Daemon': 9229,
    'Inference': 11434
}

for name, port in ports.items():
    status = scan_port('127.0.0.1', port)
    print(f'   {name}: {"✅ ONLINE" if status else "❌ OFFLINE"} (port {port})')

# ──────────────────────────────────────────────
# 2. LOCAL SERVICES STATUS
# ──────────────────────────────────────────────

print('')
print('📋 LOCAL SERVICES...')
print('-' * 40)

services = {
    'Cyberdeck': 'jb-daemon.exe',
    'Node': 'node.exe',
    'Swarm': 'python.exe',
    'Inference': 'python.exe'
}

for name, proc in services.items():
    try:
        import subprocess
        result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {proc}'], capture_output=True, text=True)
        status = '✅ RUNNING' if proc in result.stdout else '❌ STOPPED'
        print(f'   {name}: {status}')
    except:
        print(f'   {name}: ⚠️ UNKNOWN')

# ──────────────────────────────────────────────
# 3. SAVE LOCAL CONFIG
# ──────────────────────────────────────────────

print('')
print('💾 SAVING LOCAL CONFIG...')
print('-' * 40)

config = {
    'timestamp': datetime.now().isoformat(),
    'network': 'local',
    'ports': ports,
    'services': {
        'master_endpoint': scan_port('127.0.0.1', 8188),
        'node': scan_port('127.0.0.1', 8545),
        'daemon': scan_port('127.0.0.1', 9229),
        'inference': scan_port('127.0.0.1', 11434)
    },
    'status': 'operational'
}

with open('C:/Aegentix/local_network.json', 'w') as f:
    json.dump(config, f, indent=2)

print('   ✅ Config saved: C:/Aegentix/local_network.json')

# ──────────────────────────────────────────────
# 4. FINAL STATUS
# ──────────────────────────────────────────────

print('')
print('============================================================')
print('📊 LOCAL NETWORK STATUS')
print('============================================================')
print(f'   Master Endpoint: {"ONLINE" if scan_port("127.0.0.1", 8188) else "OFFLINE"}')
print(f'   Node: {"ONLINE" if scan_port("127.0.0.1", 8545) else "OFFLINE"}')
print(f'   Daemon: {"ONLINE" if scan_port("127.0.0.1", 9229) else "OFFLINE"}')
print(f'   Inference: {"ONLINE" if scan_port("127.0.0.1", 11434) else "OFFLINE"}')
print('============================================================')
print('🜂 LOCAL NETWORK — DEPLOYED')
