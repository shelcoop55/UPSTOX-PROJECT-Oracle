
import sys
import os
from pathlib import Path

# Add project root
sys.path.append(str(Path(__file__).resolve().parent))

from backend.services.market_data.snapshot_service import SnapshotService

DB_PATH = Path("market_data.db").absolute()

def test_snapshot():
    print("🚀 Testing Snapshot Service...")
    try:
        service = SnapshotService(str(DB_PATH))
        # Use known valid params
        res = service.fetch_option_snapshot("CRUDE OIL", "2026-02-17")
        print(f"Result: {res}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_snapshot()
