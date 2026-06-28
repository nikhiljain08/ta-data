"""Unit tests for the configuration layer."""

import textwrap
from pathlib import Path

import pytest

from app.config.settings import Settings, SyncSettings, TallySettings


class TestTallySettings:
    def test_defaults(self) -> None:
        s = TallySettings()
        assert s.host == "localhost"
        assert s.port == 9000
        assert s.base_url == "http://localhost:9000"

    def test_base_url_custom_host_port(self) -> None:
        s = TallySettings(host="192.168.1.10", port=9001)
        assert s.base_url == "http://192.168.1.10:9001"


class TestSyncSettings:
    def test_entity_order_defaults(self) -> None:
        s = SyncSettings()
        assert s.entity_order[0] == "company"
        assert s.entity_order[-1] == "voucher"

    def test_invalid_batch_size_raises(self) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            SyncSettings(batch_size=0)

    def test_invalid_bulk_insert_raises(self) -> None:
        with pytest.raises(ValueError, match="positive integer"):
            SyncSettings(bulk_insert_size=-1)


class TestSettingsFromYaml:
    def test_from_nonexistent_yaml_uses_defaults(self, tmp_path: Path) -> None:
        s = Settings.from_yaml(tmp_path / "missing.yaml")
        assert s.tally.host == "localhost"

    def test_from_yaml_overrides_defaults(self, tmp_path: Path) -> None:
        yaml_content = textwrap.dedent("""\
            tally:
              host: "192.168.1.5"
              port: 9001
            sync:
              batch_size: 250
        """)
        cfg = tmp_path / "config.yaml"
        cfg.write_text(yaml_content)
        s = Settings.from_yaml(cfg)
        assert s.tally.host == "192.168.1.5"
        assert s.tally.port == 9001
        assert s.sync.batch_size == 250

    def test_env_var_overrides_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        yaml_content = "tally:\n  host: yaml-host\n"
        cfg = tmp_path / "config.yaml"
        cfg.write_text(yaml_content)
        monkeypatch.setenv("TALLYSYNC_TALLY__HOST", "env-host")
        s = Settings.from_yaml(cfg)
        assert s.tally.host == "env-host"

    def test_invalid_log_level_raises(self, tmp_path: Path) -> None:
        yaml_content = "logging:\n  level: VERBOSE\n"
        cfg = tmp_path / "config.yaml"
        cfg.write_text(yaml_content)
        with pytest.raises(Exception):
            Settings.from_yaml(cfg)


class TestSettingsSecurityDefaults:
    def test_verify_ssl_default_true(self) -> None:
        s = Settings()
        assert s.security.verify_ssl is True

    def test_api_bound_to_localhost(self) -> None:
        s = Settings()
        assert s.api.host == "127.0.0.1"
