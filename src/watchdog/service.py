"""
Watchdog-Service für SentinelClaw.

Unabhängiger Überwachungsprozess der bei Anomalien automatisch den
Kill-Switch auslöst. Prüft alle 10 Sekunden:
1. Scan-Timeouts (DB-basiert)
2. OpenShell-Sandbox-Gesundheit
3. API-Health-Check
4. Scope-Verletzungen
5. Kill-Vervollständigung
Siehe docs/KILL_SWITCH.md Abschnitt 7.
"""

import asyncio
import subprocess
from datetime import UTC, datetime

from src.shared.config import Settings, get_settings
from src.shared.database import DatabaseManager
from src.shared.kill_switch import KillSwitch
from src.shared.logging_setup import get_logger
from src.shared.repositories import ScanJobRepository
from src.shared.types.models import ScanJob, ScanStatus

logger = get_logger(__name__)

# API-Health-Endpoint (Container-Netzwerk)
_HEALTH_URL = "http://sentinelclaw-api:3001/health"


class Watchdog:
    """Überwacht SentinelClaw und löst bei Anomalien den Kill-Switch aus."""

    CHECK_INTERVAL: int = 10
    MAX_HEALTH_FAILURES: int = 3
    DEFAULT_MAX_SCAN_DURATION: int = 600

    def __init__(self) -> None:
        self._health_failures: int = 0
        self._running: bool = True
        self._settings: Settings = get_settings()
        self._db: DatabaseManager | None = None
        self._scan_repo: ScanJobRepository | None = None

    async def _initialize(self) -> None:
        """Erstellt DB-Verbindung beim Start."""
        self._db = DatabaseManager(self._settings.db_path)
        await self._db.initialize()
        self._scan_repo = ScanJobRepository(self._db)

    async def run(self) -> None:
        """Hauptschleife — läuft bis stop() aufgerufen wird."""
        await self._initialize()
        logger.info(
            "watchdog_started",
            check_interval=self.CHECK_INTERVAL,
            max_scan_duration=self.DEFAULT_MAX_SCAN_DURATION,
        )
        while self._running:
            try:
                await self._check_all()
            except Exception as exc:
                logger.error("watchdog_check_error", error=str(exc))
            await asyncio.sleep(self.CHECK_INTERVAL)
        await self._shutdown()

    async def _shutdown(self) -> None:
        """Schliesst DB-Verbindung beim Beenden."""
        if self._db is not None:
            await self._db.close()
        logger.info("watchdog_stopped")

    def stop(self) -> None:
        """Signalisiert der Hauptschleife, sich zu beenden."""
        self._running = False

    async def _check_all(self) -> None:
        """Führt alle Prüfungen in einem Durchlauf aus."""
        await self._check_scan_timeouts()
        self._check_openshell_health()
        self._check_app_health()
        await self._check_scope_violations()
        self._check_kill_completion()

    # -- Prüfung 1: Scan-Timeouts ------------------------------------------

    async def _check_scan_timeouts(self) -> None:
        """Killt Scans die länger als max_duration laufen."""
        if self._scan_repo is None:
            return

        running_scans: list[ScanJob] = await self._scan_repo.list_by_status(
            ScanStatus.RUNNING,
        )
        now = datetime.now(UTC)

        for scan in running_scans:
            if scan.started_at is None:
                continue
            max_duration: int = scan.config.get(
                "max_duration", self.DEFAULT_MAX_SCAN_DURATION,
            )
            elapsed = (now - scan.started_at).total_seconds()

            if elapsed > max_duration:
                logger.warning(
                    "watchdog_scan_timeout",
                    scan_id=str(scan.id),
                    elapsed_seconds=elapsed,
                    max_duration=max_duration,
                )
                self._execute_kill(
                    f"Scan {scan.id} überschreitet maximale Dauer: "
                    f"{elapsed:.0f}s > {max_duration}s",
                    scan_id=str(scan.id),
                )
                await self._scan_repo.update_status(
                    scan.id, ScanStatus.EMERGENCY_KILLED,
                )

    # -- Prüfung 2: OpenShell-Sandbox-Gesundheit ----------------------------

    def _check_openshell_health(self) -> None:
        """Prüft ob die OpenShell-Sandbox erreichbar ist."""
        try:
            result = subprocess.run(
                ["openshell", "status"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode != 0 or "Connected" not in result.stdout:
                logger.warning(
                    "watchdog_openshell_unhealthy",
                    output=result.stdout[:200],
                )
        except FileNotFoundError:
            pass  # openshell nicht installiert — im Container-Kontext normal
        except Exception as exc:
            logger.debug("watchdog_openshell_check_failed", error=str(exc))

    # -- Prüfung 3: API-Health-Check ----------------------------------------

    def _check_app_health(self) -> None:
        """Killt nach MAX_HEALTH_FAILURES aufeinanderfolgenden Fehlern."""
        try:
            result = subprocess.run(
                ["curl", "-sf", "--max-time", "5", _HEALTH_URL],
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                if self._health_failures > 0:
                    logger.info(
                        "watchdog_health_recovered",
                        previous_failures=self._health_failures,
                    )
                self._health_failures = 0
                return
            self._health_failures += 1
            logger.warning(
                "watchdog_health_failed",
                consecutive_failures=self._health_failures,
                max_allowed=self.MAX_HEALTH_FAILURES,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
            self._health_failures += 1
            logger.warning(
                "watchdog_health_error",
                error=str(exc),
                consecutive_failures=self._health_failures,
            )

        if self._health_failures >= self.MAX_HEALTH_FAILURES:
            self._execute_kill(
                f"API antwortet nicht "
                f"({self._health_failures} aufeinanderfolgende Fehler)",
            )

    # -- Prüfung 4: Scope-Verletzungen -------------------------------------

    async def _check_scope_violations(self) -> None:
        """Prüft ob laufende Scans noch im Scope sind."""
        if self._scan_repo is None:
            return
        from src.watchdog.scope_checks import check_scope_violations
        await check_scope_violations(self._scan_repo, self._settings)

    # -- Prüfung 5: Kill-Vervollständigung ----------------------------------

    def _check_kill_completion(self) -> None:
        """Prüft ob nach Kill-Aktivierung die Sandbox tatsächlich gestoppt ist."""
        kill_switch = KillSwitch()
        if not kill_switch.is_active():
            return

        # Prüfen ob OpenShell-Sandbox noch läuft
        try:
            result = subprocess.run(
                ["openshell", "sandbox", "list"],
                capture_output=True, text=True, timeout=10,
            )
            if "Ready" in result.stdout:
                logger.critical(
                    "watchdog_kill_escalation",
                    reason="Sandbox läuft noch nach Kill-Aktivierung",
                )
                # Sandbox erneut löschen
                kill_switch._stop_openshell_sandbox()
        except Exception:
            pass

    # -- Kill-Ausführung ---------------------------------------------------

    def _execute_kill(self, reason: str, scan_id: str | None = None) -> None:
        """Aktiviert den zentralen KillSwitch."""
        logger.critical("watchdog_executing_kill", reason=reason)
        KillSwitch().activate("watchdog", reason)

        from src.watchdog.webhook import send_webhook_notification
        asyncio.ensure_future(
            send_webhook_notification(
                event="kill_switch_activated",
                reason=reason,
                scan_id=scan_id,
            ),
        )
