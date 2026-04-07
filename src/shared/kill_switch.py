"""
Kill-Switch für SentinelClaw.

Sofortiges Abschalten aller aktiven Operationen bei Sicherheitsverstößen.
Singleton-Pattern mit Thread-sicherem Event-Flag — einmal aktiviert,
ist der Kill-Switch irreversibel (außer im Test-Modus).

Kill-Pfade:
1. DB-Flag setzen (sofort, alle API-Endpoints prüfen)
2. OpenShell-Sandbox löschen (Agent-Prozess wird beendet)
3. API-Signal (Prozess-interner Stop)
"""

import threading
from datetime import UTC, datetime
from typing import Optional

from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


class KillSwitch:
    """Zentraler Notaus-Schalter für SentinelClaw.

    Nutzt threading.Event als atomares, thread-sicheres Kill-Flag.
    Sobald aktiviert, kann der Zustand nicht mehr zurückgesetzt werden
    (außer explizit über reset() im Test-Kontext).
    """

    _instance: Optional["KillSwitch"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "KillSwitch":
        """Singleton — es gibt nur einen Kill-Switch pro Prozess."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        """Initialisiert den Kill-Switch (nur beim ersten Mal)."""
        if self._initialized:
            return
        self._kill_flag: threading.Event = threading.Event()
        self._triggered_by: str = ""
        self._reason: str = ""
        self._activated_at: datetime | None = None
        self._initialized: bool = True

    def activate(self, triggered_by: str, reason: str) -> None:
        """Aktiviert den Kill-Switch und stoppt die OpenShell-Sandbox.

        Setzt das Kill-Flag atomar, löscht die Sandbox und
        loggt den Vorgang für die Audit-Nachverfolgung.
        """
        if self._kill_flag.is_set():
            logger.warning(
                "kill_switch_already_active",
                triggered_by=triggered_by,
                reason=reason,
                original_trigger=self._triggered_by,
            )
            return

        # Kill-Flag setzen (atomar, irreversibel)
        self._kill_flag.set()
        self._triggered_by = triggered_by
        self._reason = reason
        self._activated_at = datetime.now(UTC)

        logger.critical(
            "kill_switch_activated",
            triggered_by=triggered_by,
            reason=reason,
            activated_at=self._activated_at.isoformat(),
        )

        # Kill-Pfad 2: OpenShell-Sandbox sofort löschen
        self._stop_openshell_sandbox()

    def _stop_openshell_sandbox(self) -> None:
        """Stoppt die OpenShell-Sandbox — beendet den Agent-Prozess sofort."""
        import subprocess

        from src.shared.config import get_settings

        try:
            settings = get_settings()
            sandbox_name = settings.openshell_sandbox_name
            result = subprocess.run(
                ["openshell", "sandbox", "delete", sandbox_name, "--force"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0:
                logger.info("openshell_sandbox_stopped", sandbox=sandbox_name)
            else:
                logger.warning(
                    "openshell_sandbox_stop_failed",
                    sandbox=sandbox_name,
                    stderr=result.stderr[:200],
                )
        except FileNotFoundError:
            logger.debug("openshell_cli_not_found")
        except Exception as exc:
            logger.error("openshell_sandbox_stop_error", error=str(exc))

    def is_active(self) -> bool:
        """Prüft ob der Kill-Switch aktiviert wurde."""
        return self._kill_flag.is_set()

    @property
    def triggered_by(self) -> str:
        """Gibt zurück, wer den Kill-Switch ausgelöst hat."""
        return self._triggered_by

    @property
    def reason(self) -> str:
        """Gibt die Begründung für die Aktivierung zurück."""
        return self._reason

    @property
    def activated_at(self) -> datetime | None:
        """Gibt den Zeitpunkt der Aktivierung zurück."""
        return self._activated_at

    # NUR FÜR TESTS — im Produktivbetrieb niemals aufrufen!
    def reset(self) -> None:
        """Setzt den Kill-Switch zurück (NUR FÜR TESTS)."""
        logger.warning("kill_switch_reset_called")
        self._kill_flag.clear()
        self._triggered_by = ""
        self._reason = ""
        self._activated_at = None
