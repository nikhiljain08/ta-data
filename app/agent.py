"""Top-level Agent — wires together scheduler, sync engine, and control API.

Lifecycle
---------
Agent.start() blocks until interrupted (SIGINT/SIGTERM or SCM stop signal).
The Windows Service wrapper calls start() in a background thread and calls
stop() from the service's SvcStop handler.
"""

import threading

from loguru import logger

from app.config.settings import Settings


class Agent:
    """Composition root for the TallySync agent."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stop_event = threading.Event()

    def start(self) -> None:
        logger.info("TallySync agent starting", version="0.1.0")
        self._stop_event.clear()

        # Modules wired here once implemented:
        #   self._db    = build_engine(self._settings.database)
        #   self._sched = build_scheduler(self._settings, self._db)
        #   self._api   = build_api(self._settings.api)

        logger.info("Agent running — press Ctrl+C to stop")
        try:
            self._stop_event.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        logger.info("TallySync agent stopping")
        self._stop_event.set()
        # Teardown order: scheduler → sync engine → DB connection pool → API
