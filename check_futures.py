import sqlite3
import pandas as pd
from datetime import datetime

db_path = "market_data.db"
conn = sqlite3.connect(db_path)

# query futures
df = pd.read_sql("SELECT symbol, expiry, instrument_key FROM instruments WHERE segment_id='NSE_FO' AND type_code='FUT'", conn)
conn.close()

print(f"Total Futures: {len(df)}")
print(df.head())

# unique symbols
print(f"Unique Symbols: {df['symbol'].nunique()}")
print(df['symbol'].unique()[:10])

# Check expirations
print("\nExpirations sample:")
print(df['expiry'].dropna().sort_values().unique()[:5])
