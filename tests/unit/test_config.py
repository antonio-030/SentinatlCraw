"""Unit-Tests für die Konfiguration."""

import os

from src.shared.config import Settings


def test_default_settings():
    """Prüft dass Default-Werte korrekt geladen werden."""
    settings = Settings(
        _env_file=None,  # Keine .env Datei laden
    )
    assert settings.llm_provider == "claude-abo"
    assert settings.log_level == "INFO"
    assert settings.mcp_port == 8080
    assert settings.sandbox_timeout == 300
    assert settings.max_concurrent_scans == 1
    assert settings.sandbox_cpu_limit == 2.0


def test_allowed_targets_parsing():
    """Prüft dass komma-separierte Targets korrekt geparsed werden."""
    settings = Settings(
        allowed_targets="10.10.10.0/24, 192.168.1.0/24",
        _env_file=None,
    )
    targets = settings.get_allowed_targets_list()
    assert len(targets) == 2
    assert "10.10.10.0/24" in targets
    assert "192.168.1.0/24" in targets


def test_empty_targets():
    """Prüft dass leere Targets eine leere Liste ergeben."""
    settings = Settings(allowed_targets="", _env_file=None)
    assert settings.get_allowed_targets_list() == []


def test_has_claude_key():
    """Prüft die Claude-Key-Erkennung."""
    # Kein Key
    settings = Settings(claude_api_key="", _env_file=None)
    assert settings.has_claude_key() is False

    # Platzhalter-Key
    settings = Settings(claude_api_key="sk-ant-DEIN_KEY_HIER", _env_file=None)
    assert settings.has_claude_key() is False

    # Echter Key
    settings = Settings(claude_api_key="sk-ant-real-key-123", _env_file=None)
    assert settings.has_claude_key() is True
