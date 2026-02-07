
import sys
import os
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).resolve().parent))

from backend.services.market_data.snapshot_service import SnapshotService

DB_PATH = Path("market_data.db").absolute()

def refresh_all_major():
    print("🚀 Manual Snapshot Refresh...")
    try:
        service = SnapshotService(str(DB_PATH))
        # Refresh for Crude Oil Near Future
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, expiry FROM instrument_master WHERE name='CRUDE OIL' AND instrument_type='FUT' AND is_active=1 LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        
        if row:
            res = service.fetch_option_snapshot(row[0], row[1])
            print(f"✅ Success: {res}")
        else:
            print("❌ No active Crude Oil found to refresh.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    refresh_all_major()
