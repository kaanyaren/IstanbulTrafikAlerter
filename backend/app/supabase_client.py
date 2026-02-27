"""
Supabase Client — Singleton wrapper for the Python worker.

Uses service_role key for full write access (bypasses RLS).
"""

from __future__ import annotations

import logging
from supabase import create_client, Client

from app.config import settings

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_supabase_client() -> Client:
    """Return a singleton Supabase client using the service_role key."""
    global _client
    if _client is None:
        _client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        logger.info("Supabase client initialized: %s", settings.SUPABASE_URL)
    return _client
