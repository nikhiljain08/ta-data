"""CLI entry-point for the TallySync agent.

Commands
--------
tally-sync run          Start the sync agent (foreground)
tally-sync service      Windows Service management sub-commands
tally-sync sync         Trigger a manual sync
tally-sync status       Print last sync status
"""

import click


@click.group()
@click.version_option()
def cli() -> None:
    """TallySync — TallyPrime synchronization agent."""


@cli.command()
@click.option("--config", default="config.yaml", help="Path to config file.")
def run(config: str) -> None:
    """Start the sync agent in the foreground."""
    from app.config.settings import Settings

    settings = Settings.from_yaml(config)

    from app.logging.setup import configure_logging

    configure_logging(settings.logging)

    from app.agent import Agent

    agent = Agent(settings)
    agent.start()


@cli.group()
def service() -> None:
    """Windows Service management."""


@service.command("install")
def service_install() -> None:
    """Install TallySync as a Windows Service."""
    from app.windows_service.installer import install

    install()


@service.command("uninstall")
def service_uninstall() -> None:
    """Uninstall the TallySync Windows Service."""
    from app.windows_service.installer import uninstall

    uninstall()


@service.command("start")
def service_start() -> None:
    """Start the TallySync Windows Service."""
    from app.windows_service.installer import start

    start()


@service.command("stop")
def service_stop() -> None:
    """Stop the TallySync Windows Service."""
    from app.windows_service.installer import stop

    stop()


if __name__ == "__main__":
    cli()
