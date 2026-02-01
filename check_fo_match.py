import sqlite3
import re

db_path = "market_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get 5 F&O records
print("--- F&O Sample ---")
rows = cursor.execute("SELECT symbol, trading_symbol, type_code FROM instruments WHERE segment_id='NSE_FO' LIMIT 5").fetchall()
for r in rows:
    print(r)

# Logic to extract underlying from Futures
print("\n--- Futures Extraction ---")
# FUT symbols are usually like "RELIANCE24FEB..."
# But wait, looking at the previous output: "NATIONALUM 355 PE..."
# It seems `symbol` column contains spaces. It's likely `Underlying Strike Type Expiry`.
# But for FUT it might be `Underlying Expiry`.
# Let's check FUT symbols specifically.
fut_rows = cursor.execute("SELECT symbol, trading_symbol, instrument_key FROM instruments WHERE segment_id='NSE_FO' AND type_code='FUT' LIMIT 5").fetchall()
for r in fut_rows:
    print(r)
    
# Strategy: 
# The `symbol` column for futures seems to start with the underlying name.
# Let's try to split by space and take the first part?
# Example: "NATIONALUM 24 FEB 26 FUT" (Guessing format)
# If the first part matches an NSE_EQ symbol, we have a match.
    
print("\n--- Matching Attempt ---")
# Get all active NSE_EQ symbols
eq_symbols = set([r[0] for r in cursor.execute("SELECT symbol FROM instruments WHERE segment_id='NSE_EQ'").fetchall()])

# Get all NSE_FO symbols
fo_symbols = [r[0] for r in cursor.execute("SELECT symbol FROM instruments WHERE segment_id='NSE_FO'").fetchall()]

matched_set = set()
for fsym in fo_symbols:
    # Try getting first word
    parts = fsym.split(' ')
    candidate = parts[0]
    if candidate in eq_symbols:
        matched_set.add(candidate)

print(f"Matched {len(matched_set)} unique underlying stocks.")
print(f"Sample: {list(matched_set)[:10]}")

conn.close()
