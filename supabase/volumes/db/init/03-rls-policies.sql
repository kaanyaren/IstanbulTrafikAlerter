-- ============================================================================
-- 03-rls-policies.sql
-- Row Level Security policies.
-- Current setup: Public read access (anon), service_role for writes.
-- Auth can be layered on later.
-- ============================================================================

-- ── Enable RLS on all tables ────────────────────────────────────────────────
ALTER TABLE traffic_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE events        ENABLE ROW LEVEL SECURITY;
ALTER TABLE predictions   ENABLE ROW LEVEL SECURITY;

-- ── traffic_zones ───────────────────────────────────────────────────────────
-- Anyone can read zones
CREATE POLICY "traffic_zones_select_public"
    ON traffic_zones FOR SELECT
    TO anon, authenticated, service_role, supabase_admin
    USING (true);

-- Only service_role (Python worker) can insert/update/delete
CREATE POLICY "traffic_zones_insert_service"
    ON traffic_zones FOR INSERT
    TO supabase_admin, service_role
    WITH CHECK (true);

CREATE POLICY "traffic_zones_update_service"
    ON traffic_zones FOR UPDATE
    TO supabase_admin, service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "traffic_zones_delete_service"
    ON traffic_zones FOR DELETE
    TO supabase_admin, service_role
    USING (true);

-- ── events ──────────────────────────────────────────────────────────────────
-- Anyone can read events
CREATE POLICY "events_select_public"
    ON events FOR SELECT
    TO anon, authenticated, service_role, supabase_admin
    USING (true);

-- Only service_role can write
CREATE POLICY "events_insert_service"
    ON events FOR INSERT
    TO supabase_admin, service_role
    WITH CHECK (true);

CREATE POLICY "events_update_service"
    ON events FOR UPDATE
    TO supabase_admin, service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "events_delete_service"
    ON events FOR DELETE
    TO supabase_admin, service_role
    USING (true);

-- ── predictions ─────────────────────────────────────────────────────────────
-- Anyone can read predictions
CREATE POLICY "predictions_select_public"
    ON predictions FOR SELECT
    TO anon, authenticated, service_role, supabase_admin
    USING (true);

-- Only service_role can write
CREATE POLICY "predictions_insert_service"
    ON predictions FOR INSERT
    TO supabase_admin, service_role
    WITH CHECK (true);

CREATE POLICY "predictions_update_service"
    ON predictions FOR UPDATE
    TO supabase_admin, service_role
    USING (true) WITH CHECK (true);

CREATE POLICY "predictions_delete_service"
    ON predictions FOR DELETE
    TO supabase_admin, service_role
    USING (true);

-- ── Grant table permissions to roles ────────────────────────────────────────
GRANT SELECT ON traffic_zones, events, predictions TO anon;
GRANT SELECT ON traffic_zones, events, predictions TO authenticated;
GRANT ALL    ON traffic_zones, events, predictions TO service_role;
GRANT ALL    ON traffic_zones, events, predictions TO supabase_admin;
