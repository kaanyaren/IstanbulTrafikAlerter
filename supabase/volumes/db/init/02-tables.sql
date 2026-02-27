-- ============================================================================
-- 02-tables.sql
-- Core tables: traffic_zones, events, predictions
-- Matches the existing SQLAlchemy models exactly.
-- ============================================================================

-- ── traffic_zones ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS traffic_zones (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    name                   VARCHAR(255) NOT NULL UNIQUE,
    polygon                geometry(POLYGON, 4326) NOT NULL,
    base_congestion_level  DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    rush_hour_multiplier   DOUBLE PRECISION NOT NULL DEFAULT 1.5
);

CREATE INDEX IF NOT EXISTS ix_traffic_zones_name     ON traffic_zones (name);
CREATE INDEX IF NOT EXISTS ix_traffic_zones_polygon  ON traffic_zones USING GIST (polygon);

-- ── events ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    name        VARCHAR(255) NOT NULL,
    description TEXT,
    venue_name  VARCHAR(255) NOT NULL,
    location    geometry(POINT, 4326) NOT NULL,
    start_time  TIMESTAMPTZ NOT NULL,
    end_time    TIMESTAMPTZ,
    capacity    INTEGER,
    category    VARCHAR(50) NOT NULL,   -- concert | sports | conference | other
    source      VARCHAR(100) NOT NULL,
    source_id   VARCHAR(255) NOT NULL,
    updated_at  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS ix_events_start_time          ON events (start_time);
CREATE INDEX IF NOT EXISTS ix_events_category             ON events (category);
CREATE UNIQUE INDEX IF NOT EXISTS ix_events_source_source_id ON events (source, source_id);
CREATE INDEX IF NOT EXISTS ix_events_location             ON events USING GIST (location);

-- ── predictions ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    zone_id          UUID NOT NULL REFERENCES traffic_zones(id) ON DELETE CASCADE,
    event_id         UUID REFERENCES events(id) ON DELETE SET NULL,
    predicted_at     TIMESTAMPTZ NOT NULL,
    target_time      TIMESTAMPTZ NOT NULL,
    congestion_score INTEGER NOT NULL CHECK (congestion_score BETWEEN 0 AND 100),
    confidence       DOUBLE PRECISION NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    factors          JSONB
);

CREATE INDEX IF NOT EXISTS ix_predictions_zone_id        ON predictions (zone_id);
CREATE INDEX IF NOT EXISTS ix_predictions_target_time    ON predictions (target_time);
CREATE INDEX IF NOT EXISTS ix_predictions_zone_target    ON predictions (zone_id, target_time);

-- ── Enable Realtime for these tables ────────────────────────────────────────
-- PostgREST & Supabase Realtime will pick up changes via logical replication.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'supabase_realtime') THEN
        CREATE PUBLICATION supabase_realtime;
    END IF;
END
$$;
ALTER PUBLICATION supabase_realtime ADD TABLE predictions;
ALTER PUBLICATION supabase_realtime ADD TABLE events;
ALTER PUBLICATION supabase_realtime ADD TABLE traffic_zones;
