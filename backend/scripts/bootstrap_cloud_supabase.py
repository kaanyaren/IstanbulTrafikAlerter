"""
Bootstrap cloud Supabase PostgreSQL schema for Istanbul Traffic Alerter.

What it does:
1) Verifies DB connectivity via SQLAlchemy async engine
2) Ensures required extensions (postgis, pgcrypto)
3) Creates ORM tables (events, traffic_zones, predictions)
4) Creates/updates RPC function: get_latest_predictions
"""

import asyncio

from sqlalchemy import text

from app.database import engine
from app.models import Base


def _rpc_statements() -> list[str]:
        return [
                """
                create or replace function public.get_latest_predictions()
                returns setof public.predictions
                language sql
                stable
                as $$
                  select p.*
                  from public.predictions p
                  join (
                          select zone_id, max(target_time) as max_target_time
                          from public.predictions
                          group by zone_id
                  ) latest
                        on latest.zone_id = p.zone_id
                   and latest.max_target_time = p.target_time
                  order by p.target_time desc;
                $$;
                """,
                "grant execute on function public.get_latest_predictions() to anon",
                "grant execute on function public.get_latest_predictions() to authenticated",
                "grant execute on function public.get_latest_predictions() to service_role",
        ]


def _access_statements() -> list[str]:
        return [
                "grant usage on schema public to anon, authenticated, service_role",
                "grant all privileges on all tables in schema public to service_role",
                "grant select on table public.traffic_zones to anon, authenticated",
                "grant select on table public.events to anon, authenticated",
                "grant select on table public.predictions to anon, authenticated",
                "alter table public.traffic_zones enable row level security",
                "alter table public.events enable row level security",
                "alter table public.predictions enable row level security",
                "drop policy if exists traffic_zones_read_all on public.traffic_zones",
                "drop policy if exists events_read_all on public.events",
                "drop policy if exists predictions_read_all on public.predictions",
                (
                        "create policy traffic_zones_read_all "
                        "on public.traffic_zones for select using (true)"
                ),
                "create policy events_read_all on public.events for select using (true)",
                (
                        "create policy predictions_read_all "
                        "on public.predictions for select using (true)"
                ),
                "notify pgrst, 'reload schema'",
        ]


def _defaults_statements() -> list[str]:
        return [
                "alter table public.traffic_zones alter column id set default gen_random_uuid()",
                "alter table public.events alter column id set default gen_random_uuid()",
                "alter table public.predictions alter column id set default gen_random_uuid()",
                "alter table public.traffic_zones alter column created_at set default timezone('utc', now())",
                "alter table public.events alter column created_at set default timezone('utc', now())",
                "alter table public.predictions alter column created_at set default timezone('utc', now())",
        ]


async def main() -> None:
    async with engine.begin() as conn:
        check = await conn.execute(text("select 1"))
        print("db_ok", check.scalar())

        await conn.execute(text("create extension if not exists postgis"))
        await conn.execute(text("create extension if not exists pgcrypto"))
        print("extensions_ok")

        await conn.run_sync(Base.metadata.create_all)
        print("tables_ok")

        for stmt in _defaults_statements():
            await conn.execute(text(stmt))
        print("defaults_ok")

        for stmt in _access_statements():
            await conn.execute(text(stmt))
        print("access_ok")

        for stmt in _rpc_statements():
            await conn.execute(text(stmt))
        print("rpc_ok")

    await engine.dispose()
    print("bootstrap_done")


if __name__ == "__main__":
    asyncio.run(main())
