
import logging
import time
import sys
from upstox_client.feeder.market_data_streamer_v3 import MarketDataStreamerV3
from backend.utils.auth.manager import AuthManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SDKWSTest")

def on_message(data):
    feeds = data.get("feeds", {})
    for key, tick in feeds.items():
        depth = tick.get("depth", {})
        buy = depth.get("buy", [])
        sell = depth.get("sell", [])
        
        if buy or sell:
            logger.info(f"--- SDK DEPTH FOR {key} ---")
            logger.info(f"Bids: {len(buy)} | Asks: {len(sell)}")
            if len(buy) > 5:
                logger.info("CORE DETECTED: Depth > 5 levels via SDK D30!")
                # Print first 10 levels
                for i in range(min(10, len(buy))):
                    print(f"Level {i+1}: {buy[i]['price']} x {buy[i]['quantity']}")
            else:
                logger.info("Only 5 levels received. D30 mode might not be active or supported for this symbol.")

def on_open():
    logger.info("SDK Streamer Opened")

def on_error(error):
    logger.error(f"SDK Streamer Error: {error}")

def run_test():
    auth = AuthManager()
    token = auth.get_valid_token()
    
    # We need a dummy api_client with configuration
    import upstox_client
    config = upstox_client.Configuration()
    config.access_token = token
    api_client = upstox_client.ApiClient(config)
    
    # MCX is OPEN now (18:12 IST approx) - testing with Crude Oil
    streamer = MarketDataStreamerV3(api_client, ["MCX_FO|472789"], mode="full_d30")
    
    streamer.on("message", on_message)
    streamer.on("open", on_open)
    streamer.on("error", on_error)
    
    logger.info("Connecting SDK Streamer...")
    streamer.connect()
    
    # Run for 20s
    time.sleep(20)
    streamer.disconnect()

if __name__ == "__main__":
    run_test()
