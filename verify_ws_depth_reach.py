
import logging
import sys
import time
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

from backend.services.streaming.websocket_v3_streamer import WebSocketV3Streamer
from upstox_client.feeder.proto import MarketDataFeedV3_pb2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WSDepthTest")

class DepthTester(WebSocketV3Streamer):
    def _on_message(self, ws, message):
        if isinstance(message, bytes):
            decoded_data = MarketDataFeedV3_pb2.FeedResponse()
            decoded_data.ParseFromString(message)
            
            # Direct inspection of Protobuf object
            for key, tick in decoded_data.feeds.items():
                if tick.HasField("fullFeed") and tick.fullFeed.HasField("marketFF"):
                    mlevel = tick.fullFeed.marketFF.marketLevel
                    raw_len = len(mlevel.bidAskQuote)
                    if raw_len > 0:
                        logger.info(f"RAW PROTOBUF DEPTH FOR {key}: {raw_len} levels")
            
        super()._on_message(ws, message)

    def _process_tick_data(self, data: dict):
        feeds = data.get("feeds", {})
        for key, tick in feeds.items():
            # In Upstox V3 Protobuf -> Dict, depth is usually inside market_full or similar
            # The exact structure depends on how json_format.MessageToDict maps it.
            # Based on MarketDataFeedV3_pb2: FullFeed -> market_full -> market_level -> depth
            mf = tick.get("marketFull", {})
            ml = mf.get("marketLevel", {})
            depth = ml.get("depth", {})
            
            buy = depth.get("buy", [])
            sell = depth.get("sell", [])
            
            if buy or sell:
                logger.info(f"--- DEPTH FOR {key} ---")
                logger.info(f"Bids: {len(buy)} | Asks: {len(sell)}")
                if len(buy) > 5:
                    logger.info(f"SUCCESS: Depth > 5 levels ({len(buy)})!")
                    # Print level 6 to 15 if available
                    for i in range(5, min(15, len(buy))):
                        print(f"Level {i+1}: {buy[i]['price']} x {buy[i]['quantity']}")

def run_test():
    tester = DepthTester()
    if tester.connect():
        logger.info("Connected. Subscribing to RELIANCE and CRUDE OIL...")
        # Subscribe to instruments in D30 mode
        tester.subscribe(["MCX_FO|472789", "NSE_EQ|INE002A01018"], mode="full_d30")
        
        # Run for 20 seconds
        time.sleep(20)
        tester.disconnect()
    else:
        logger.error("Failed to connect.")

if __name__ == "__main__":
    run_test()
