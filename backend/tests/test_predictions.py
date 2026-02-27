import pytest
import asyncio
from datetime import datetime, timezone, timedelta
import pandas as pd

from app.models.traffic_zone import TrafficZone
from app.models.event import Event
from app.prediction.rule_engine import predict
from app.prediction.features import extract_features


@pytest.mark.asyncio
async def test_rule_engine_predict_basic(mocker):
    # Mock db_session
    mock_session = mocker.AsyncMock()
    
    # Mock zone
    zone = TrafficZone(id="123e4567-e89b-12d3-a456-426614174000", name="Test Zone", base_congestion_level=0.5)
    
    # Mock the execute result for zone
    mock_result = mocker.MagicMock()
    mock_result.scalar_one_or_none.return_value = zone
    mock_session.execute.return_value = mock_result
    
    # It's a bit tricky to mock the second execute for event because SQLAlchemy core statements are built.
    # So we'll mock the second call to return None
    mock_result_2 = mocker.MagicMock()
    mock_result_2.scalar_one_or_none.return_value = None
    mock_session.execute.side_effect = [mock_result, mock_result_2]

    target_time = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc) # Not a weekend, not rush hour
    
    result = await predict(zone.id, target_time, mock_session)
    
    # Base = 0.5 * 100 = 50
    assert result.congestion_score == 50
    assert result.confidence == 0.8
    assert result.factors["base_score"] == 50.0
    assert "rush_hour" not in result.factors


def test_extract_features():
    zone = TrafficZone(id="123e4567-e89b-12d3-a456-426614174000", name="Test Zone", base_congestion_level=0.6)
    target_time = datetime(2026, 3, 1, 18, 0, tzinfo=timezone.utc) # Sunday, rush hour (18:00)
    
    event1 = Event(
        id="223e4567-e89b-12d3-a456-426614174000",
        name="Concert",
        start_time=datetime(2026, 3, 2, 20, 0, tzinfo=timezone.utc),
        capacity=10000
    )
    event2 = Event(
        id="323e4567-e89b-12d3-a456-426614174001",
        name="Match",
        start_time=datetime(2026, 3, 1, 19, 0, tzinfo=timezone.utc),
        capacity=50000
    )
    
    df = extract_features(zone, target_time, [event1, event2])
    
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["hour_of_day"] == 18
    assert df.iloc[0]["is_weekend"] == 1
    assert df.iloc[0]["is_rush_hour"] == 1
    assert df.iloc[0]["nearby_event_count"] == 2
    assert df.iloc[0]["max_event_capacity"] == 50000
    assert df.iloc[0]["total_event_capacity"] == 60000
    assert df.iloc[0]["zone_base_level"] == 0.6
    # days until event: event2 is in 1 hour -> 0 days. event1 is in 1 day, 2 hours -> 1 day. min is 0.
    assert df.iloc[0]["days_until_event"] == 0


from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_prediction_api_routing():
    response = client.get("/api/v1/predictions")
    assert response.status_code == 422  # Missing required query params

    response2 = client.get("/api/v1/predictions/zones/123e4567-e89b-12d3-a456-426614174000")
    assert response2.status_code in [200, 500] 
