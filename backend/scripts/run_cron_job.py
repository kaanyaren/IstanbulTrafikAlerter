"""
Run Istanbul Traffic Alerter data jobs without a long-running worker.

Designed for GitHub Actions cron usage.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from typing import Iterable

# Ensure backend/app is importable when script runs from repository root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.tasks.events import _fetch_and_store_events
from app.tasks.predictions import generate_predictions


logger = logging.getLogger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run scheduled data jobs once.")
    parser.add_argument(
        "--mode",
        choices=["events", "predictions", "all"],
        default="all",
        help="Which job group to run.",
    )
    return parser.parse_args()


def _modes(mode: str) -> Iterable[str]:
    if mode == "all":
        return ("events", "predictions")
    return (mode,)


async def _run(mode: str) -> None:
    if mode == "events":
        logger.info("Starting events job...")
        await _fetch_and_store_events()
        logger.info("Events job completed.")
        return

    if mode == "predictions":
        logger.info("Starting predictions job...")
        await generate_predictions()
        logger.info("Predictions job completed.")
        return

    raise ValueError(f"Unknown mode: {mode}")


async def main() -> None:
    args = _parse_args()
    for mode in _modes(args.mode):
        await _run(mode)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
