"""Configuration layer.

Precedence (highest → lowest)
------------------------------
1. Environment variables  TALLYSYNC_<SECTION>__<KEY>  (e.g. TALLYSYNC_DATABASE__URL)
2. config.yaml
3. Pydantic field defaults

The YAML source is injected as a custom PydanticBaseSettingsSource so the
standard pydantic-settings priority chain (env > yaml > defaults) is
respected.  Calling model_validate() directly would bypass env vars entirely,
which is why we use the full __init__ path via from_yaml().

Secrets policy
--------------
* Database passwords and API keys must NOT appear in config.yaml.
* Set them as environment variables or store them in the Windows Credential
  Manager (keyring).  The settings object fetches from keyring automatically
  when security.use_keyring=True and the env var is absent.
"""

from __future__ import annotations

import contextvars
from pathlib import Path
from typing import Any

import keyring
import yaml
from pydantic import Field, field_validator, model_validator
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# ── YAML source ───────────────────────────────────────────────────────────────

# Thread-safe context variable so that from_yaml() works correctly even when
# called concurrently (e.g. from tests running in parallel).
_yaml_path_ctx: contextvars.ContextVar[Path] = contextvars.ContextVar(
    "tallysync_yaml_path", default=Path("config.yaml")
)


class _YamlConfigSource(PydanticBaseSettingsSource):
    """Pydantic-settings source that reads from a YAML file."""

    def __init__(self, settings_cls: type[BaseSettings], path: Path) -> None:
        super().__init__(settings_cls)
        self._data: dict[str, Any] = {}
        if path.exists():
            with path.open("r", encoding="utf-8") as fh:
                self._data = yaml.safe_load(fh) or {}

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        value = self._data.get(field_name)
        return value, field_name, False

    def field_is_complex(self, field: FieldInfo) -> bool:
        return True

    def __call__(self) -> dict[str, Any]:
        return self._data


# ── Sub-models ────────────────────────────────────────────────────────────────


class TallySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    host: str = "localhost"
    port: int = 9000
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_backoff_base: float = 2.0
    retry_backoff_max: float = 60.0
    company_name: str = ""

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    url: str = "postgresql+psycopg://tallysync:tallysync@localhost:5432/tallysync"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    echo_sql: bool = False


class SyncSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    batch_size: int = 500
    bulk_insert_size: int = 1000
    full_sync_on_startup: bool = False
    incremental_interval_minutes: int = 15
    full_sync_cron: str = "0 2 * * *"
    voucher_from_date: str = ""
    entity_order: list[str] = Field(
        default=[
            "company",
            "ledger_group",
            "unit",
            "stock_group",
            "godown",
            "voucher_type",
            "stock_item",
            "ledger",
            "voucher",
        ]
    )

    @field_validator("batch_size", "bulk_insert_size")
    @classmethod
    def must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("must be a positive integer")
        return v


class RetrySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    max_attempts: int = 5
    dead_letter_after: int = 3


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8765
    enabled: bool = True


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    level: str = "INFO"
    rotation: str = "10 MB"
    retention: str = "30 days"
    log_dir: str = "logs"
    structured: bool = True

    @field_validator("level")
    @classmethod
    def valid_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            raise ValueError(f"log level must be one of {allowed}")
        return v.upper()


class SecuritySettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    use_keyring: bool = True
    verify_ssl: bool = True


class MonitoringSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    emit_sync_stats: bool = True
    stats_interval_seconds: int = 60


# ── Root settings ─────────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """Root configuration object.

    Use Settings.from_yaml(path) for production.
    Direct keyword-argument construction is supported in tests.
    """

    model_config = SettingsConfigDict(
        env_prefix="TALLYSYNC_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    tally: TallySettings = Field(default_factory=TallySettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    sync: SyncSettings = Field(default_factory=SyncSettings)
    retry: RetrySettings = Field(default_factory=RetrySettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        **kwargs: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        yaml_path = _yaml_path_ctx.get()
        return (
            init_settings,  # highest: direct kwargs (for tests)
            env_settings,  # second:  real environment variables
            dotenv_settings,  # third:   .env file
            _YamlConfigSource(settings_cls, yaml_path),  # fourth: config.yaml
        )

    @model_validator(mode="after")
    def _resolve_secrets_from_keyring(self) -> Settings:
        if self.security.use_keyring:
            _maybe_inject_db_url_from_keyring(self.database)
        return self

    @classmethod
    def from_yaml(cls, path: str | Path = "config.yaml") -> Settings:
        """Load settings from YAML with env vars taking priority."""
        token = _yaml_path_ctx.set(Path(path))
        try:
            return cls()
        finally:
            _yaml_path_ctx.reset(token)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _maybe_inject_db_url_from_keyring(db: DatabaseSettings) -> None:
    """Replace placeholder password in DB URL with keyring-stored credential."""
    stored = keyring.get_password("tallysync", "db_url")
    if stored:
        db.url = stored
