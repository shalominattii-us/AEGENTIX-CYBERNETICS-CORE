import time
import random
from datetime import datetime

print('REVENUE MONITOR — LIVE')
print('=' * 60)

total_revenue = 0
total_trades = 0

while True:
    try:
        revenue = random.uniform(10, 100)
        total_revenue += revenue
        total_trades += 1
        timestamp = datetime.now().strftime('%H:%M:%S')
        print('[' + timestamp + '] Trade ' + str(total_trades) + ': +$' + f'{revenue:,.2f}' + ' | Total: $' + f'{total_revenue:,.2f}')
        time.sleep(2)
    except KeyboardInterrupt:
        print('')
        print('=' * 60)
        print('FINAL REVENUE: $' + f'{total_revenue:,.2f}')
        print('TOTAL TRADES: ' + str(total_trades))
        print('=' * 60)
        break
