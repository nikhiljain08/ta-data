from __future__ import annotations

"""Windows Service installer helpers called from the CLI (app.main)."""

try:
    import win32serviceutil

    from app.windows_service.service import TallySyncService

    def install() -> None:
        """Install TallySync as a Windows Service."""
        win32serviceutil.InstallService(
            TallySyncService._svc_name_,
            TallySyncService._svc_display_name_,
            startType=2,  # SERVICE_AUTO_START
        )
        print(f"Service '{TallySyncService._svc_display_name_}' installed.")

    def uninstall() -> None:
        """Remove the TallySync Windows Service."""
        win32serviceutil.RemoveService(TallySyncService._svc_name_)
        print(f"Service '{TallySyncService._svc_display_name_}' removed.")

    def start() -> None:
        """Start the TallySync Windows Service."""
        win32serviceutil.StartService(TallySyncService._svc_name_)
        print(f"Service '{TallySyncService._svc_display_name_}' started.")

    def stop() -> None:
        """Stop the TallySync Windows Service."""
        win32serviceutil.StopService(TallySyncService._svc_name_)
        print(f"Service '{TallySyncService._svc_display_name_}' stopped.")

except ImportError:

    def install() -> None:  # type: ignore[misc]
        raise RuntimeError("pywin32 is required to manage Windows Services")

    def uninstall() -> None:  # type: ignore[misc]
        raise RuntimeError("pywin32 is required to manage Windows Services")

    def start() -> None:  # type: ignore[misc]
        raise RuntimeError("pywin32 is required to manage Windows Services")

    def stop() -> None:  # type: ignore[misc]
        raise RuntimeError("pywin32 is required to manage Windows Services")
