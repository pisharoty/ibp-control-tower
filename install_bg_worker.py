import re
import os

bg_worker_code = '''
# --- AUTOMATED 5-MINUTE BACKGROUND PRICE SYNCHRONIZER ---
import threading
import time

_BG_WORKER_STARTED = False

def launch_background_ticker_sync(interval_seconds=300):
    """Launch a background daemon thread to refresh live market prices every 5 minutes."""
    global _BG_WORKER_STARTED
    if not _BG_WORKER_STARTED:
        _BG_WORKER_STARTED = True
        
        def _sync_loop():
            while True:
                time.sleep(interval_seconds)
                try:
                    import update_live_prices
                    update_live_prices.sync_all_commodity_tickers()
                except Exception:
                    pass
                    
        worker = threading.Thread(target=_sync_loop, daemon=True)
        worker.start()

# Initialize background worker upon module load
launch_background_ticker_sync(300)
'''

target = "robot_feeds.py" if os.path.exists("robot_feeds.py") else "robot_feeds.txt"

with open(target, "r") as f:
    code = f.read()

if "launch_background_ticker_sync" not in code:
    code = bg_worker_code.strip() + "\n\n" + code
    with open(target, "w") as f:
        f.write(code)
    print(f"✅ Background 5-minute synchronizer successfully installed in {target}.")
else:
    print(f"ℹ️ Background worker is already present in {target}.")
