import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DB_PATH = "market_data.db"

def get_expiries(commodity, inst_type='FUT'):
    """Replicating the logic from mcx_live.py"""
    if not commodity: return []
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        query = "SELECT DISTINCT expiry FROM instrument_master WHERE segment = 'MCX_FO' AND name = ? AND is_active = 1"
        params = [commodity]
        
        if inst_type == 'FUT':
            query += " AND instrument_type = 'FUT'"
        elif inst_type == 'OPT':
            query += " AND (instrument_type = 'CE' OR instrument_type = 'PE')"
            
        query += " ORDER BY expiry"
        
        cursor.execute(query, params)
        rows = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        return rows
    except Exception as e:
        print(f"Error fetching expiries: {e}")
        return []

def main():
    print("--- Verifying Expiry Logic ---")
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found at {DB_PATH}")
        return

    test_cases = [
        ('GOLD', 'FUT'),
        ('GOLD', 'OPT'),
        ('NATURALGAS', 'FUT'),
        ('NATURALGAS', 'OPT'),
        ('CRUDE OIL', 'FUT')
    ]

    for comm, itype in test_cases:
        print(f"\nQuerying: {comm} [{itype}]")
        expiries = get_expiries(comm, itype)
        if expiries:
            print(f"✅ Found {len(expiries)} expiries. First 3: {expiries[:3]}")
        else:
            print(f"❌ No expiries found!")

if __name__ == "__main__":
    main()
