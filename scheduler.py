"""
Scheduler for Naukri Automation
---------------------------------
Runs the automation every day at 09:00 AM.

Usage:
    python scheduler.py          — Starts the scheduler (keeps running)
    python scheduler.py --now    — Runs the automation immediately (one-shot)

For a more robust setup on Windows, you can use Task Scheduler instead.
See README.md for instructions.
"""

import sys
import time
import logging
from datetime import datetime

import schedule

from naukri_automation import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

SCHEDULED_TIME = "09:00"  # 24-hour format


def job() -> None:
    """Wrapper that logs the trigger and runs the automation."""
    logger.info("Scheduled job triggered at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    try:
        run()
    except Exception as e:
        logger.error("Job failed: %s", e)


def main() -> None:
    # If --now flag is passed, run immediately and exit
    if "--now" in sys.argv:
        logger.info("Running automation immediately (--now flag)...")
        job()
        return

    # Schedule daily at the configured time
    schedule.every().day.at(SCHEDULED_TIME).do(job)

    logger.info("Naukri automation scheduler started.")
    logger.info("Next run scheduled at %s every day.", SCHEDULED_TIME)
    logger.info("Press Ctrl+C to stop.\n")

    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")


if __name__ == "__main__":
    main()
