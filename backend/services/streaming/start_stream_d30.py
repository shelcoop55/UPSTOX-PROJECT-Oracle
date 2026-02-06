
import logging
import sys
import time
import sqlite3
from pathlib import Path
from typing import List

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.services.streaming.websocket_v3_streamer import WebSocketV3Streamer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('market_feed_d30.log')
    ]
)
logger = logging.getLogger("MarketFeedD30")

DB_PATH = Path("market_data.db").absolute()

def get_active_mcx_keys() -> List[str]:
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT instrument_key, trading_symbol FROM instrument_master WHERE segment = 'MCX_FO' AND is_active = 1 AND instrument_type = 'FUT'")
        rows = cursor.fetchall()
        conn.close()
        
        keys = [row[0] for row in rows]
        logger.info(f"Found {len(keys)} active MCX instruments: {[row[1] for row in rows]}")
        return keys
    except Exception as e:
        logger.error(f"Error fetching MCX keys: {e}")
        return []

def main():
    logger.info("🚀 Starting Market Feed (D30 Mode)...")
    
    streamer = WebSocketV3Streamer(db_path=str(DB_PATH))
    
    if streamer.connect():
        # Get active MCX keys
        keys = get_active_mcx_keys()
        
        # Also add NIFTY/BANKNIFTY for good measure if available
        keys.extend(["NSE_INDEX|Nifty 50", "NSE_INDEX|Nifty Bank"])
        
        # Initial Subscription (Futures + Nifty)
        initial_keys = set(keys)
        current_subscriptions = set()
        
        # Helper to sync subscriptions
        def sync_subscriptions():
            try:
                # 1. Get Watched Keys from DB
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT instrument_key FROM watched_instruments")
                watched = set(row[0] for row in cursor.fetchall())
                conn.close()
                
                # 2. Add Fixed Keys (Futures)
                target_set = initial_keys.union(watched)
                
                # 3. Calculate Diff
                to_subscribe = list(target_set - current_subscriptions)
                to_unsubscribe = list(current_subscriptions - target_set)
                
                # 4. Action
                if to_subscribe:
                    logger.info(f"➕ Adding {len(to_subscribe)} new keys...")
                    # Batch subscribe if needed
                    for i in range(0, len(to_subscribe), 50):
                        batch = to_subscribe[i:i+50]
                        streamer.subscribe(batch, mode="full_d30")
                        time.sleep(0.1)
                    current_subscriptions.update(to_subscribe)
                    
                if to_unsubscribe:
                    logger.info(f"➖ Removing {len(to_unsubscribe)} keys...")
                    streamer.unsubscribe(to_unsubscribe)
                    current_subscriptions.difference_update(to_unsubscribe)
                    
            except Exception as e:
                logger.error(f"Sync Error: {e}")

        # Ensure initial sync happens immediately
        sync_subscriptions()

        logger.info("✅ Market Feed Active. Monitoring for dynamic subscriptions...")
            
        try:
            while True:
                status = streamer.get_health_status()
                # Periodic Re-Sync every 3 seconds
                sync_subscriptions()
                
                # Log health occasionally (every 30s roughly)
                if int(time.time()) % 30 == 0:
                     logger.info(f"❤️ Health: {status} | Subs: {len(current_subscriptions)}")
                
                time.sleep(3)
        except KeyboardInterrupt:
            logger.info("🛑 Stopping feed...")
        else:
            logger.warning("⚠️ No instruments to subscribe to!")
        
        streamer.disconnect()
    else:
        logger.error("❌ Failed to connect to Upstox WebSocket.")

if __name__ == "__main__":
    main()
