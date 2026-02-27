"""
E2E Test — Supabase entegrasyonunu doğrular.

1. Supabase bağlantısını test eder
2. Fake prediction verisini Supabase'e yazar
3. Veriyi geri okuyarak doğrular
4. Temizler

Kullanım:
  python -m scripts.test_supabase_e2e
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings


def main():
    from supabase import create_client

    print("=" * 60)
    print("Istanbul Traffic Alerter — Supabase E2E Test")
    print("=" * 60)

    # 1. Connect
    print(f"\n[1/5] Connecting to Supabase: {settings.SUPABASE_URL}")
    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    print("  ✓ Connected")

    # 2. Check traffic_zones exist
    print("\n[2/5] Checking traffic_zones table...")
    zones = client.table("traffic_zones").select("id, name").limit(5).execute()
    print(f"  ✓ Found {len(zones.data)} zones")
    for z in zones.data:
        print(f"    - {z['name']} ({z['id'][:8]}...)")

    if not zones.data:
        print("  ✗ No zones found. Did the seed data run? Aborting.")
        sys.exit(1)

    # 3. Insert a fake prediction
    print("\n[3/5] Inserting test prediction...")
    test_zone_id = zones.data[0]["id"]
    test_prediction = {
        "zone_id": test_zone_id,
        "predicted_at": datetime.now(timezone.utc).isoformat(),
        "target_time": datetime.now(timezone.utc).isoformat(),
        "congestion_score": 42,
        "confidence": 0.85,
        "factors": {"test": True, "source": "e2e_test"},
    }
    insert_result = client.table("predictions").insert(test_prediction).execute()
    prediction_id = insert_result.data[0]["id"]
    print(f"  ✓ Inserted prediction: {prediction_id[:8]}...")

    # 4. Read it back
    print("\n[4/5] Reading prediction back...")
    read_result = (
        client.table("predictions")
        .select("*")
        .eq("id", prediction_id)
        .execute()
    )
    assert len(read_result.data) == 1, "Expected 1 prediction, got " + str(len(read_result.data))
    pred = read_result.data[0]
    assert pred["congestion_score"] == 42
    assert pred["confidence"] == 0.85
    print(f"  ✓ Read back: score={pred['congestion_score']}, confidence={pred['confidence']}")

    # 5. Test RPC function
    print("\n[5/5] Testing RPC: get_latest_predictions...")
    rpc_result = client.rpc("get_latest_predictions").execute()
    print(f"  ✓ RPC returned {len(rpc_result.data)} predictions")

    # Cleanup
    print("\n[Cleanup] Deleting test prediction...")
    client.table("predictions").delete().eq("id", prediction_id).execute()
    print("  ✓ Cleaned up")

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
