
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
        cursor.execute("SELECT instrument_key, trading_symbol FROM instrument_master WHERE segment = 'MCX_FO' AND is_active = 1")
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
        
        if keys:
            BATCH_SIZE = 50
            logger.info(f"📡 Subscribing to {len(keys)} instruments in batches of {BATCH_SIZE}...")
            
            for i in range(0, len(keys), BATCH_SIZE):
                batch = keys[i:i+BATCH_SIZE]
                try:
                    streamer.subscribe(batch, mode="full_d30")
                    time.sleep(0.2) # Avoid rate limits
                except Exception as e:
                    logger.error(f"Failed to subscribe to batch {i}: {e}")
            
            logger.info("✅ All batches sent. Feed active. Press Ctrl+C to stop.")
            try:
                while True:
                    status = streamer.get_health_status()
                    logger.info(f"❤️ Health: {status}")
                    time.sleep(10)
            except KeyboardInterrupt:
                logger.info("🛑 Stopping feed...")
        else:
            logger.warning("⚠️ No instruments to subscribe to!")
        
        streamer.disconnect()
    else:
        logger.error("❌ Failed to connect to Upstox WebSocket.")

if __name__ == "__main__":
    main()
