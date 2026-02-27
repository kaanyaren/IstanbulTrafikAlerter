from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "traffic_alerter",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.events",
        "app.tasks.traffic",
        "app.tasks.predictions"
    ]
)

celery_app.conf.beat_schedule = {
    "fetch-events-every-6-hours": {
        "task": "app.tasks.events.fetch_events_task",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "fetch-traffic-every-15-minutes": {
        "task": "app.tasks.traffic.fetch_traffic_task",
        "schedule": crontab(minute="*/15"),
    },
    "run-predictions-every-hour": {
        "task": "app.tasks.predictions.run_predictions_task",
        "schedule": crontab(minute=0),
    },
}

celery_app.conf.timezone = "Europe/Istanbul"
