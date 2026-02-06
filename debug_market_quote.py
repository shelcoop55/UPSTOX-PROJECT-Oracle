import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path("market_data.db").absolute()

def get_screener_data(segment=None, sector=None, industry=None, index=None, search=None, limit=1000):
    """Fetch filtered data joined with latest quotes if available"""
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Base Query
        query = """
            SELECT 
                im.trading_symbol,
                im.name,
                im.sector,
                im.instrument_key,
                q.close as last_price
            FROM instrument_master im
            LEFT JOIN market_quota_nse500_data q ON im.instrument_key = q.instrument_key
        """
        
        # Dynamic Join for Index (replicating CURRENT logic in market_quote.py)
        if index and index != "All" and segment != "NSE_INDEX":
            query += " JOIN index_mapping idx ON im.instrument_key = idx.instrument_key"
            
        query += " WHERE im.is_active = 1"
        params = []
        
        if segment:
            query += " AND im.segment = ?"
            params.append(segment)
            
        # Index Filter
        if index and index != "All":
            if segment == "NSE_INDEX":
                pass
            else:
                query += " AND idx.index_name = ?"
                params.append(index)

        if sector and sector != "All":
            query += " AND im.sector = ?"
            params.append(sector)
            
        if industry and industry != "All":
            query += " AND im.industry = ?"
            params.append(industry)
            
        if search:
            query += " AND (im.trading_symbol LIKE ? OR im.name LIKE ?)"
            match = f"%{search}%"
            params.extend([match, match])
            
        query += " ORDER BY im.trading_symbol LIMIT ?"
        params.append(limit)
        
        print(f"Executing SQL: {query}")
        print(f"Params: {params}")
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        return df
        
    except Exception as e:
        print(f"Error fetching screener data: {e}")
        return pd.DataFrame()

print("--- TEST 1: Default Filters (NSE_EQ) ---")
df1 = get_screener_data(segment="NSE_EQ")
print(f"Rows: {len(df1)}")
if not df1.empty:
    print(df1.head())
else:
    print("NO DATA FOUND for NSE_EQ")

print("\n--- TEST 2: NSE_INDEX Segment ---")
df2 = get_screener_data(segment="NSE_INDEX")
print(f"Rows: {len(df2)}")
if not df2.empty:
    print(df2.head())
else:
    print("NO DATA FOUND for NSE_INDEX")

print("\n--- TEST 3: Database Integrity Check ---")
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("SELECT count(*) FROM instrument_master WHERE segment='NSE_EQ' AND is_active=1")
print(f"Active NSE_EQ instruments: {c.fetchone()[0]}")
c.execute("SELECT count(*) FROM market_quota_nse500_data")
print(f"Rows in market_data (quote): {c.fetchone()[0]}")
conn.close()
