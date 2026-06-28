from __future__ import annotations

import threading

from loguru import logger

# pywin32 is only available on Windows; guard import so non-Windows CI works.
try:
    import win32event
    import win32service
    import win32serviceutil

    class TallySyncService(win32serviceutil.ServiceFramework):
        """Windows Service wrapper for the TallySync agent.

        Install:   python -m app.windows_service.service install
        Start:     python -m app.windows_service.service start
        Stop:      python -m app.windows_service.service stop
        Remove:    python -m app.windows_service.service remove
        """

        _svc_name_ = "TallySync"
        _svc_display_name_ = "TallySync Agent"
        _svc_description_ = "Synchronises TallyPrime accounting data to PostgreSQL."

        def __init__(self, args: list[str]) -> None:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self._stop_event = win32event.CreateEvent(None, 0, 0, None)
            self._agent_thread: threading.Thread | None = None
            self._agent: object | None = None

        def SvcStop(self) -> None:  # noqa: N802
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self._stop_event)
            if self._agent is not None:
                self._agent.stop()  # type: ignore[attr-defined]

        def SvcDoRun(self) -> None:  # noqa: N802
            from app.agent import Agent
            from app.config.settings import Settings
            from app.logging.setup import configure_logging

            settings = Settings.from_yaml("config.yaml")
            configure_logging(settings.logging)

            self._agent = Agent(settings)
            self._agent_thread = threading.Thread(
                target=self._agent.start,  # type: ignore[attr-defined]
                daemon=True,
                name="tallysync-agent",
            )
            self._agent_thread.start()
            logger.info("TallySync Windows Service started")

            # Block until SCM signals stop
            win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)
            logger.info("TallySync Windows Service stopping")

except ImportError:
    # Non-Windows environment — provide a stub so imports don't fail.
    class TallySyncService:  # type: ignore[no-redef]
        _svc_name_ = "TallySync"
        _svc_display_name_ = "TallySync Agent"
