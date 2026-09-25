# ============================================================
# PERSISTENT GAIA SERVICE
# ============================================================

import time
import json
import urllib.request
from datetime import datetime

print('')
print('🔄 PERSISTENT GAIA SERVICE')
print('=' * 60)
print('   Running in background...')
print('')

while True:
    try:
        # Check Gaia status
        gaia_status = {}
        endpoints = {
            'primary': 'https://gaia.network/api/v1',
            'backup': 'https://gaia-backup.network/api/v1',
            'sovereign': 'https://sovereign.gaia.network/api/v1'
        }
        
        for name, url in endpoints.items():
            try:
                req = urllib.request.Request(url)
                response = urllib.request.urlopen(req, timeout=3)
                gaia_status[name] = 'ONLINE'
            except:
                gaia_status[name] = 'OFFLINE'
        
        # Save status
        status = {
            'timestamp': datetime.now().isoformat(),
            'status': gaia_status,
            'online': sum(1 for s in gaia_status.values() if s == 'ONLINE')
        }
        
        with open('C:/Aegentix/gaia_heartbeat.json', 'w') as f:
            json.dump(status, f, indent=2)
        
        online = sum(1 for s in gaia_status.values() if s == 'ONLINE')
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 💓 Gaia heartbeat ({online}/3 online)')
        time.sleep(30)
        
    except KeyboardInterrupt:
        print('')
        print('🛑 Gaia service stopped')
        break
    except Exception as e:
        print(f'❌ Error: {e}')
        time.sleep(5)
