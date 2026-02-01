import sqlite3

db_path = "market_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count NSE EQ stocks that have derivatives
cursor.execute("""
    SELECT count(*) 
    FROM instruments 
    WHERE segment_id='NSE_EQ' 
    AND symbol IN (SELECT DISTINCT symbol FROM instruments WHERE segment_id='NSE_FO')
""")
print(f"NSE EQ stocks with F&O: {cursor.fetchone()[0]}")

conn.close()
