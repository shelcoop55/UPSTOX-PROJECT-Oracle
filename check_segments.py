import sqlite3

db_path = "market_data.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Segments & Counts ---")
cursor.execute("SELECT segment_id, count(*) FROM instruments GROUP BY segment_id")
for row in cursor.fetchall():
    print(row)

print("\n--- NSE_FO Type Codes ---")
cursor.execute("SELECT type_code, count(*) FROM instruments WHERE segment_id='NSE_FO' GROUP BY type_code")
for row in cursor.fetchall():
    print(row)

conn.close()
