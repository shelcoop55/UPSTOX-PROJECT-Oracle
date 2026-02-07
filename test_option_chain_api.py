
import sys
import os
import requests
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from backend.utils.auth.manager import AuthManager

DB_PATH = Path("market_data.db").absolute()
# Checks out: https://upstox.com/developer/api-documentation/get-pc-option-chain
# URL pattern: https://api.upstox.com/v2/option/chain
# Params: instrument_key, expiry_date

def test_chain_api():
    print("🚀 Testing Option Chain API...")
    
    # 1. Auth
    auth = AuthManager(db_path=str(DB_PATH))
    token = auth.get_valid_token()
    if not token:
        print("❌ No token.")
        return

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    
    # 2. Key for CRUDE OIL (Future or Underlying?)
    # Usually we pass the 'underlying_key' or the 'instrument_key' of the future?
    # Documentation says: "instrument_key: Key of the instrument" (e.g. NSE_INDEX|Nifty 50)
    # For MCX, maybe the Future key? MCX_FO|CRUDEOIL...
    # Let's try passing a Future Key and see if it returns the chain.
    
    future_key = "MCX_FO|487655" # Example from logs (Crude Oil) or query DB
    
    # Let's get a real active key
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Get Underlying Key and Expiry from an actual Option
    cursor.execute("SELECT underlying_key, expiry FROM instrument_master WHERE name='CRUDE OIL' AND instrument_type='CE' ORDER BY expiry LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("❌ No Crude Oil Option found.")
        return
        
    instr_key, expiry = row
    print(f"Testing with Underlying: {instr_key} | Expiry: {expiry}")
    
    instr_key, expiry = row
    print(f"Testing Batch Quote for Expiry: {expiry}")
    
    # Get ALL Option Keys for this Expiry
    conn = sqlite3.connect(DB_PATH) # Re-open
    cursor = conn.cursor()
    cursor.execute("SELECT instrument_key FROM instrument_master WHERE name='CRUDE OIL' AND expiry=? AND instrument_type IN ('CE', 'PE')", (expiry,))
    keys = [r[0] for r in cursor.fetchall()]
    conn.close()
    
    print(f"Found {len(keys)} option contracts in DB.")
    if not keys: 
        return

    # Batch them (Upstox limit is 100 or 500? Use 100 to be safe)
    batch = keys[:50] # Test first 50
    keys_str = ",".join(batch)
    
    # API Call: Full Market Quote
    # URL: https://api.upstox.com/v2/market-quote/quotes
    url = "https://api.upstox.com/v2/market-quote/quotes"
    params = {
        "instrument_key": keys_str
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            quotes = data.get("data", {})
            print(f"Received {len(quotes)} quotes.")
            
            if quotes:
                first_key = list(quotes.keys())[0]
                print("Sample Quote:")
                print(json.dumps(quotes[first_key], indent=2))
        else:
            print(f"❌ API Error: {resp.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_chain_api()
