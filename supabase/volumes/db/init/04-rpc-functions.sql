-- ============================================================================
-- 04-rpc-functions.sql
-- Custom PostGIS RPC functions for Supabase.
-- Called from Flutter/PostgREST via: supabase.rpc('function_name', params)
-- ============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- get_predictions_nearby
-- Returns predictions for zones within a given radius of a point.
-- Usage: supabase.rpc('get_predictions_nearby', { lat, lon, radius_km, target_ts })
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_predictions_nearby(
    p_lat        DOUBLE PRECISION,
    p_lon        DOUBLE PRECISION,
    p_radius_km  DOUBLE PRECISION DEFAULT 5.0,
    p_target_ts  TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    prediction_id       UUID,
    zone_id             UUID,
    zone_name           VARCHAR(255),
    congestion_score    INTEGER,
    confidence          DOUBLE PRECISION,
    target_time         TIMESTAMPTZ,
    predicted_at        TIMESTAMPTZ,
    factors             JSONB,
    event_id            UUID,
    zone_centroid_lat   DOUBLE PRECISION,
    zone_centroid_lon   DOUBLE PRECISION,
    distance_km         DOUBLE PRECISION
)
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
    SELECT
        p.id              AS prediction_id,
        z.id              AS zone_id,
        z.name            AS zone_name,
        p.congestion_score,
        p.confidence,
        p.target_time,
        p.predicted_at,
        p.factors,
        p.event_id,
        ST_Y(ST_Centroid(z.polygon))  AS zone_centroid_lat,
        ST_X(ST_Centroid(z.polygon))  AS zone_centroid_lon,
        ST_Distance(
            ST_Centroid(z.polygon)::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
        ) / 1000.0                     AS distance_km
    FROM predictions p
    JOIN traffic_zones z ON p.zone_id = z.id
    WHERE ST_DWithin(
        z.polygon::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
        p_radius_km * 1000
    )
    AND (
        p_target_ts IS NULL
        OR p.target_time = (
            SELECT pp.target_time
            FROM predictions pp
            WHERE pp.zone_id = z.id
            ORDER BY ABS(EXTRACT(EPOCH FROM (pp.target_time - p_target_ts)))
            LIMIT 1
        )
    )
    ORDER BY distance_km;
$$;

-- Grant execute to anon so Flutter (PostgREST) can call it
GRANT EXECUTE ON FUNCTION get_predictions_nearby TO anon, authenticated;

-- ─────────────────────────────────────────────────────────────────────────────
-- get_events_nearby
-- Returns events within a given radius of a point.
-- Usage: supabase.rpc('get_events_nearby', { lat, lon, radius_km })
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_events_nearby(
    p_lat        DOUBLE PRECISION,
    p_lon        DOUBLE PRECISION,
    p_radius_km  DOUBLE PRECISION DEFAULT 5.0,
    p_category   VARCHAR DEFAULT NULL,
    p_start_date TIMESTAMPTZ DEFAULT NULL,
    p_end_date   TIMESTAMPTZ DEFAULT NULL
)
RETURNS TABLE (
    event_id     UUID,
    name         VARCHAR(255),
    description  TEXT,
    venue_name   VARCHAR(255),
    category     VARCHAR(50),
    start_time   TIMESTAMPTZ,
    end_time     TIMESTAMPTZ,
    capacity     INTEGER,
    source       VARCHAR(100),
    lat          DOUBLE PRECISION,
    lon          DOUBLE PRECISION,
    distance_km  DOUBLE PRECISION
)
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
    SELECT
        e.id          AS event_id,
        e.name,
        e.description,
        e.venue_name,
        e.category,
        e.start_time,
        e.end_time,
        e.capacity,
        e.source,
        ST_Y(e.location)  AS lat,
        ST_X(e.location)  AS lon,
        ST_Distance(
            e.location::geography,
            ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography
        ) / 1000.0        AS distance_km
    FROM events e
    WHERE ST_DWithin(
        e.location::geography,
        ST_SetSRID(ST_MakePoint(p_lon, p_lat), 4326)::geography,
        p_radius_km * 1000
    )
    AND (p_category  IS NULL OR e.category  = p_category)
    AND (p_start_date IS NULL OR e.start_time >= p_start_date)
    AND (p_end_date   IS NULL OR e.start_time <= p_end_date)
    ORDER BY distance_km;
$$;

GRANT EXECUTE ON FUNCTION get_events_nearby TO anon, authenticated;

-- ─────────────────────────────────────────────────────────────────────────────
-- get_latest_predictions_per_zone
-- Returns the most recent prediction per zone (useful for heatmap overlay).
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION get_latest_predictions()
RETURNS TABLE (
    prediction_id       UUID,
    zone_id             UUID,
    zone_name           VARCHAR(255),
    congestion_score    INTEGER,
    confidence          DOUBLE PRECISION,
    target_time         TIMESTAMPTZ,
    predicted_at        TIMESTAMPTZ,
    factors             JSONB,
    zone_centroid_lat   DOUBLE PRECISION,
    zone_centroid_lon   DOUBLE PRECISION
)
LANGUAGE sql STABLE
SECURITY DEFINER
AS $$
    SELECT DISTINCT ON (p.zone_id)
        p.id              AS prediction_id,
        z.id              AS zone_id,
        z.name            AS zone_name,
        p.congestion_score,
        p.confidence,
        p.target_time,
        p.predicted_at,
        p.factors,
        ST_Y(ST_Centroid(z.polygon))  AS zone_centroid_lat,
        ST_X(ST_Centroid(z.polygon))  AS zone_centroid_lon
    FROM predictions p
    JOIN traffic_zones z ON p.zone_id = z.id
    ORDER BY p.zone_id, p.target_time DESC;
$$;

GRANT EXECUTE ON FUNCTION get_latest_predictions TO anon, authenticated;
