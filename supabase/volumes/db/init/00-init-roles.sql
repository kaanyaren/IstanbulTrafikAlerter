-- ============================================================================
-- 00-init-roles.sql
-- Creates the PostgREST roles (anon, authenticated, supabase_admin)
-- and configures the search_path for PostgREST.
-- ============================================================================

-- Roles for PostgREST
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'anon') THEN
    CREATE ROLE anon NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticated') THEN
    CREATE ROLE authenticated NOLOGIN NOINHERIT;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'service_role') THEN
    CREATE ROLE service_role NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'supabase_admin') THEN
    CREATE ROLE supabase_admin LOGIN PASSWORD 'postgres' NOINHERIT;
  END IF;
END
$$;

ALTER ROLE supabase_admin WITH LOGIN PASSWORD 'postgres';

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role, supabase_admin;

-- Allow PostgREST authenticator role
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'authenticator') THEN
    CREATE ROLE authenticator NOINHERIT LOGIN PASSWORD 'postgres';
  END IF;
END
$$;

GRANT anon TO authenticator;
GRANT authenticated TO authenticator;
GRANT service_role TO authenticator;
GRANT supabase_admin TO authenticator;

GRANT supabase_admin TO service_role;

-- Realtime schema
CREATE SCHEMA IF NOT EXISTS _realtime;

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'supabase_realtime_admin') THEN
    CREATE ROLE supabase_realtime_admin NOLOGIN NOINHERIT;
  END IF;
END
$$;

GRANT ALL ON SCHEMA _realtime TO supabase_realtime_admin;
GRANT supabase_realtime_admin TO authenticator;
