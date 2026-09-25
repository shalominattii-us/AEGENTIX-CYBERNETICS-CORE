# ============================================================
# PERSISTENT SWARM SERVICE
# ============================================================

import time
import json
from datetime import datetime

print('🔄 PERSISTENT SWARM SERVICE')
print('=' * 60)
print('   Running in background...')
print('')

while True:
    try:
        # Load swarm state
        with open('C:/Aegentix/swarm_state.json', 'r') as f:
            state = json.load(f)
        
        # Update timestamp
        state['timestamp'] = datetime.now().isoformat()
        state['status'] = 'operational'
        state['heartbeat'] = 'alive'
        
        # Save state
        with open('C:/Aegentix/swarm_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f'[{datetime.now().strftime("%H:%M:%S")}] 💓 Swarm heartbeat sent')
        time.sleep(60)
    except KeyboardInterrupt:
        print('')
        print('🛑 Swarm service stopped')
        break
    except Exception as e:
        print(f'❌ Error: {e}')
        time.sleep(5)
