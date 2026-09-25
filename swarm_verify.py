import os
import concurrent.futures

nodes = [
    'master_autonomy.py',
    'full_autonomy.py',
    'conversational_engine.py',
    'sovereign-autonomy-daemon.ps1',
    'cybercore_daemon.ps1',
    'c_drive_context.json'
]

def verify_node(node):
    path = os.path.join(r'C:\Aegentix', node)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    status = "OK" if exists else "FAIL"
    return f"[{status}] {node:<32} | Size: {size:>10} bytes"

if __name__ == "__main__":
    print("=== AEGENTIX SWARM INTEGRITY VERIFICATION ===")
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(verify_node, nodes))
    for res in results:
        print(res)
