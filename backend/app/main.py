"""
Istanbul Traffic Alerter — Worker Entry Point

Bu modül artık bir HTTP API sunmaz.
Tüm API hizmeti Supabase (PostgREST) tarafından sağlanır.
Bu dosya sadece worker'ı başlatmak için kullanılır.

Kullanım:
  celery -A app.celery_app worker --beat --loglevel=info
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)
logger.info("Istanbul Traffic Alerter Worker — API hizmeti Supabase tarafından sağlanır.")
