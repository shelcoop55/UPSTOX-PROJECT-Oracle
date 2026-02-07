
import sys
import os
import sqlite3
import requests
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.utils.auth.manager import AuthManager

DB_PATH = Path("market_data.db").absolute()
HISTORY_URL = "https://api.upstox.com/v2/historical-candle"

def get_active_futures():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT instrument_key, trading_symbol FROM instrument_master WHERE segment = 'MCX_FO' AND instrument_type = 'FUT' AND is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows

def seed_data():
    print("🚀 Seeding Offline Data (Historical Close)...")
    
    # 1. Auth
    auth = AuthManager(db_path=str(DB_PATH))
    token = auth.get_valid_token()
    if not token:
        print("❌ No valid token. Please login first.")
        return

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # 2. Get Keys
    futures = get_active_futures()
    print(f"found {len(futures)} active Futures.")
    
    conn = sqlite3.connect(DB_PATH)
    
    # 3. Fetch & Insert
    count = 0
    today = datetime.now().strftime("%Y-%m-%d")
    
    for key, symbol in futures:
        try:
            # Fetch Daily Candle (Up to today)
            # URL: /v2/historical-candle/{key}/day/{to_date}
            # formatting to_date as YYYY-MM-DD
            url = f"{HISTORY_URL}/{key}/day/{today}"
            
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                candles = data.get("data", {}).get("candles", [])
                
                if candles:
                    # Latest candle is usually first or last? Upstox documentation says:
                    # "The response array is sorted in descending order of time" -> So [0] is latest.
                    latest = candles[0]
                    
                    # [timestamp, open, high, low, close, volume, oi]
                    ts, op, hi, lo, cl, vol, oi = latest[:7]
                    
                    # Insert into websocket_ticks_v3
                    # We treat 'close' as 'ltp' for offline view
                    # timestamp needs conversion? standard format string preferred?
                    # Upstox returns ISO string usually for time? No, daily candles return '2025-02-06T00:00:00+05:30'
                    
                    sql = """
                        INSERT OR REPLACE INTO websocket_ticks_v3 
                        (instrument_key, ltp, open, high, low, close, volume, oi)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    conn.execute(sql, (key, cl, op, hi, lo, cl, vol, oi))
                    count += 1
                    print(f"✅ {symbol}: Close={cl}")
                else:
                    print(f"⚠️ {symbol}: No Data")
            else:
                print(f"❌ {symbol}: API Error {resp.status_code}")
            
            # Rate limit handling (3 requests/sec approx)
            time.sleep(0.35)
            
            if count % 10 == 0:
                conn.commit()
                
        except Exception as e:
            print(f"Error processing {symbol}: {e}")
            
    conn.commit()
    conn.close()
    print(f"\n✅ Seeded {count} instruments. Dashboard should now show data.")

if __name__ == "__main__":
    seed_data()
