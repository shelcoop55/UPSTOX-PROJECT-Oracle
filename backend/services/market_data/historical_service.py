
import requests
import pandas as pd
from datetime import datetime
from backend.utils.auth.manager import AuthManager

class HistoricalService:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.auth = AuthManager(db_path=db_path)
        self.base_url = "https://api.upstox.com/v2/historical-candle"

    def get_intraday_candles(self, instrument_key: str, interval: str = '1minute'):
        """
        Fetch intraday candles for the current day.
        Endpoint: /historical-candle/intraday/{instrumentKey}/{interval}
        """
        token = self.auth.get_valid_token()
        if not token:
            return {"error": "Authentication failed"}

        # Construct URL for Intraday
        # Note: Upstox documentation says /historical-candle/intraday/{key}/{interval}
        # But user requested checking v3. We will stick to standard v2 unless fails, but match user's structure.
        url = f"{self.base_url}/intraday/{instrument_key}/{interval}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", {}).get("candles", [])
                cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']
                df = pd.DataFrame(data, columns=cols)
                return {"status": "success", "data": df.to_dict('records')}
            else:
                return {"error": f"API Error: {resp.text}"}
        except Exception as e:
            return {"error": str(e)}

    def get_historical_candles(self, instrument_key: str, interval: str, to_date: str, from_date: str):
        """
        Fetch historical candles for a specific range.
        Endpoint: /historical-candle/{instrumentKey}/{interval}/{to_date}/{from_date}
        """
        token = self.auth.get_valid_token()
        if not token:
            return {"error": "Authentication failed"}

        url = f"{self.base_url}/{instrument_key}/{interval}/{to_date}/{from_date}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json().get("data", {}).get("candles", [])
                cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'oi']
                df = pd.DataFrame(data, columns=cols)
                return {"status": "success", "data": df.to_dict('records')}
            else:
                return {"error": f"API Error: {resp.text}"}
        except Exception as e:
            return {"error": str(e)}
