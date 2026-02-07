
import sqlite3
import requests
import logging
from typing import List, Dict
import pandas as pd
from backend.utils.auth.manager import AuthManager

logger = logging.getLogger(__name__)

class SnapshotService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.auth = AuthManager(db_path=db_path)
        
    def fetch_option_snapshot(self, commodity_name: str, expiry_date: str):
        """
        1. Get all Option Keys for (Commodity, Expiry).
        2. Call Upstox Market Quote API (Batched).
        3. Store in websocket_ticks_v3.
        """
        logger.info(f"📸 Fetching Snapshot for {commodity_name} {expiry_date}")
        
        # 1. Get Keys
        keys = self._get_keys(commodity_name, expiry_date)
        if not keys:
            logger.warning("No keys found.")
            return {"status": "no_keys", "count": 0}
            
        logger.info(f"Found {len(keys)} keys. Fetching quotes...")
        
        # 2. Batch Call (Max 100 per call usually, let's limit safely)
        BATCH_SIZE = 100
        total_updated = 0
        
        token = self.auth.get_valid_token()
        if not token:
             raise Exception("Authentication failed")
             
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        url = "https://api.upstox.com/v2/market-quote/quotes"
        
        for i in range(0, len(keys), BATCH_SIZE):
            batch = keys[i : i + BATCH_SIZE]
            keys_str = ",".join(batch)
            
            try:
                resp = requests.get(url, headers=headers, params={"instrument_key": keys_str}, timeout=5)
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    self._save_snapshot(data)
                    total_updated += len(data)
                else:
                    logger.error(f"API Error: {resp.text}")
            except Exception as e:
                logger.error(f"Batch failed: {e}")
                
        return {"status": "success", "updated": total_updated}

    def _get_keys(self, name: str, expiry: str) -> List[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Find underlying or future name? 'CRUDE OIL' usually maps to trading_symbol check or name check
        # Our frontend sends 'CRUDE OIL'.
        cursor.execute("SELECT instrument_key FROM instrument_master WHERE name=? AND expiry=? AND instrument_type IN ('CE', 'PE')", (name, expiry))
        keys = [r[0] for r in cursor.fetchall()]
        conn.close()
        return keys

    def _save_snapshot(self, quotes: Dict):
        conn = sqlite3.connect(self.db_path)
        # quotes is dict: key -> {last_price, oi, volume, ohlc: {...}, depth: {...}}
        
        data_tuples = []
        for key, q in quotes.items():
            ltp = q.get('last_price', 0)
            vol = q.get('volume', 0)
            oi = q.get('oi', 0)
            ohlc = q.get('ohlc', {})
            op = ohlc.get('open', 0)
            hi = ohlc.get('high', 0)
            lo = ohlc.get('low', 0)
            cl = ohlc.get('close', 0)
            
            # depth (v2 structure is simple)
            depth = q.get('depth', {})
            buy = depth.get('buy', [])
            sell = depth.get('sell', [])
            
            # Extract Top 1 Bid/Ask for summary
            bid = buy[0]['price'] if buy else 0
            ask = sell[0]['price'] if sell else 0
            
            data_tuples.append((
                key, ltp, vol, oi, op, hi, lo, cl, bid, ask
            ))
            
        sql = """
            INSERT OR REPLACE INTO websocket_ticks_v3 
            (instrument_key, ltp, volume, oi, open, high, low, close, bid_price_1, ask_price_1)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        conn.executemany(sql, data_tuples)
        conn.commit()
        conn.close()
