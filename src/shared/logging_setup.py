"""
Strukturiertes Logging für SentinelClaw.

Nutzt structlog für JSON-formatierte Logs mit automatischer
Secret-Maskierung. Kein console.log, kein print — immer den Logger nutzen.
"""

import re
import sys
from typing import Any

import structlog

from src.shared.constants.defaults import SECRET_PATTERNS

# Kompilierte Regex-Pattern für Secret-Erkennung (Performance)
_SECRET_REGEXES = [re.compile(pattern, re.IGNORECASE) for pattern in SECRET_PATTERNS]

# Ersetzungstext für gefundene Secrets
_REDACTED = "[REDACTED]"


def _mask_secrets(value: str) -> str:
    """Ersetzt alle erkannten Secrets in einem String durch [REDACTED]."""
    result = value
    for regex in _SECRET_REGEXES:
        result = regex.sub(_REDACTED, result)
    return result


def _mask_secrets_in_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Maskiert Secrets in allen String-Werten eines Dicts (rekursiv)."""
    masked = {}
    for key, value in data.items():
        if isinstance(value, str):
            masked[key] = _mask_secrets(value)
        elif isinstance(value, dict):
            masked[key] = _mask_secrets_in_dict(value)
        elif isinstance(value, list):
            masked[key] = [
                _mask_secrets(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            masked[key] = value
    return masked


def secret_masking_processor(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog-Processor der Secrets aus allen Log-Einträgen entfernt."""
    return _mask_secrets_in_dict(event_dict)


def setup_logging(log_level: str = "INFO") -> None:
    """Konfiguriert das strukturierte Logging für die gesamte Anwendung.

    Wird einmal beim Start aufgerufen. Alle Module nutzen danach
    get_logger() für ihre Log-Ausgaben.
    """
    structlog.configure(
        processors=[
            # Kontextdaten hinzufügen
            structlog.contextvars.merge_contextvars,
            # Log-Level hinzufügen
            structlog.stdlib.add_log_level,
            # Zeitstempel im ISO-8601 Format (UTC)
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Secrets maskieren (MUSS vor der Ausgabe kommen)
            secret_masking_processor,
            # Stack-Traces formatieren
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # JSON-Ausgabe für maschinenlesbare Logs
            structlog.processors.JSONRenderer(sort_keys=True),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            _level_name_to_int(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def _level_name_to_int(level_name: str) -> int:
    """Konvertiert Log-Level-Namen in Integer für structlog-Filter."""
    level_map = {
        "DEBUG": 10,
        "INFO": 20,
        "WARNING": 30,
        "WARN": 30,
        "ERROR": 40,
        "CRITICAL": 50,
    }
    return level_map.get(level_name.upper(), 20)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Erstellt einen benannten Logger für ein Modul.

    Nutzung in jedem Modul:
        from src.shared.logging_setup import get_logger
        logger = get_logger(__name__)
        logger.info("Scan gestartet", target="10.10.10.1")
    """
    return structlog.get_logger(name)
