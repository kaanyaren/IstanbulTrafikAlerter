import pandas as pd
from datetime import datetime
from typing import List

from app.models.traffic_zone import TrafficZone
from app.models.event import Event


def extract_features(zone: TrafficZone, target_time: datetime, events: List[Event]) -> pd.DataFrame:
    """
    Extracts features for ML model predictions.
    Features:
    - hour_of_day
    - day_of_week
    - is_weekend
    - is_rush_hour
    - nearby_event_count
    - max_event_capacity
    - total_event_capacity
    - zone_base_level
    - days_until_event
    """
    hour = target_time.hour
    day_of_week = target_time.weekday()
    # Monday is 0, Sunday is 6
    is_weekend = 1 if day_of_week >= 5 else 0
    
    is_rush_hour = 1 if (7 <= hour < 9) or (17 <= hour < 19) else 0
    
    nearby_event_count = len(events)
    max_event_capacity = max([e.capacity or 0 for e in events], default=0)
    total_event_capacity = sum([e.capacity or 0 for e in events])
    
    # Calculate days_until_event (minimum days to next event)
    # If event already started or in the past, it could be <= 0.
    days_until_list = []
    for e in events:
        delta = e.start_time - target_time
        # Return total float days or integer days? Let's use integer days.
        days_until_list.append(delta.days)
        
    days_until_event = min(days_until_list, default=999)
        
    features = {
        "zone_id": [str(zone.id)],
        "target_time": [target_time],
        "hour_of_day": [hour],
        "day_of_week": [day_of_week],
        "is_weekend": [is_weekend],
        "is_rush_hour": [is_rush_hour],
        "nearby_event_count": [nearby_event_count],
        "max_event_capacity": [max_event_capacity],
        "total_event_capacity": [total_event_capacity],
        "zone_base_level": [zone.base_congestion_level],
        "days_until_event": [days_until_event]
    }
    
    return pd.DataFrame(features)
