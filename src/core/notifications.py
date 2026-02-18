"""
Skill-completion notification monitor for Personal Skill Monitor.

Runs a daemon thread that polls the skill queue every N minutes and fires
a desktop notification when a skill is about to finish (< threshold minutes).

Usage:
    monitor = NotificationMonitor(controller, interval_minutes=5, threshold_minutes=5)
    monitor.start()
    monitor.stop()   # call on app exit
"""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.controller import AppController

logger = logging.getLogger(__name__)

try:
    from plyer import notification as _plyer_notification
    _PLYER_AVAILABLE = True
except Exception:
    _PLYER_AVAILABLE = False
    logger.info("plyer not available — desktop notifications disabled")


class NotificationMonitor:
    """
    Background daemon that watches the skill queue and fires desktop
    notifications when a skill is about to complete.

    Parameters
    ----------
    controller       : AppController instance (for queue access)
    interval_minutes : how often to check the queue (default 5)
    threshold_minutes: notify when time_left < this value (default 5)
    enabled          : master on/off switch (can be toggled at runtime)
    """

    def __init__(
        self,
        controller: "AppController",
        interval_minutes: int = 5,
        threshold_minutes: int = 5,
        enabled: bool = True,
    ) -> None:
        self.controller        = controller
        self.interval          = interval_minutes * 60   # seconds
        self.threshold         = threshold_minutes * 60  # seconds
        self.enabled           = enabled
        self._stop_event       = threading.Event()
        self._thread: threading.Thread | None = None
        self._notified: set[str] = set()   # track already-notified skills

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, name="NotificationMonitor", daemon=True
        )
        self._thread.start()
        logger.info("NotificationMonitor started (interval=%ds, threshold=%ds)",
                    self.interval, self.threshold)

    def stop(self) -> None:
        """Signal the monitor thread to stop."""
        self._stop_event.set()

    def set_enabled(self, value: bool) -> None:
        self.enabled = value
        logger.info("NotificationMonitor enabled=%s", value)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self) -> None:
        while not self._stop_event.wait(timeout=self.interval):
            if self.enabled:
                try:
                    self._check_queue()
                except Exception as exc:
                    logger.warning("NotificationMonitor error: %s", exc)

    def _check_queue(self) -> None:
        queue = self.controller.char_data.queue
        if not queue:
            return

        now = datetime.now(tz=timezone.utc)

        for entry in queue:
            finish_str = entry.get("finish_date")
            if not finish_str:
                continue

            try:
                finish_dt = datetime.fromisoformat(
                    finish_str.replace("Z", "+00:00")
                )
            except ValueError:
                continue

            time_left = (finish_dt - now).total_seconds()

            # Only notify if within threshold and not yet notified
            if 0 < time_left < self.threshold:
                skill_key = f"{entry.get('skill_id')}_{entry.get('finished_level')}"
                if skill_key not in self._notified:
                    self._notified.add(skill_key)
                    self._fire(entry, time_left)

            # Clean up old keys for skills that have finished
            elif time_left <= 0:
                skill_key = f"{entry.get('skill_id')}_{entry.get('finished_level')}"
                self._notified.discard(skill_key)

    def _fire(self, entry: dict, time_left: float) -> None:
        from src.data import skills_db  # local import to avoid circular deps

        skill_id = entry.get("skill_id", 0)
        level    = entry.get("finished_level", 0)
        name     = skills_db.get_skill_name(skill_id)
        mins     = max(1, int(time_left / 60))

        title   = "⚡ Skill finishing soon!"
        message = f"{name} Level {level} — {mins} minute(s) remaining"

        logger.info("Notification: %s", message)

        if _PLYER_AVAILABLE:
            try:
                _plyer_notification.notify(
                    title=title,
                    message=message,
                    app_name="Personal Skill Monitor",
                    timeout=10,
                )
            except Exception as exc:
                logger.warning("plyer notification failed: %s", exc)
