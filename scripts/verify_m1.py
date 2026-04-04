#!/usr/bin/env python3
"""
Meilenstein 1 — Verifizierungs-Script.

Prüft alle Voraussetzungen für M1: Setup komplett.
Ergebnis: NemoClaw + Docker lokal lauffähig, Claude verbunden.
"""

import asyncio
import sys
from pathlib import Path

# Projektroot zum Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_check(name: str, passed: bool, detail: str = "") -> None:
    """Gibt ein Prüfergebnis formatiert aus."""
    icon = "✅" if passed else "❌"
    suffix = f" — {detail}" if detail else ""
    print(f"  {icon} {name}{suffix}")


async def check_config() -> bool:
    """Prüft ob die Konfiguration geladen werden kann."""
    try:
        from src.shared.config import get_settings
        settings = get_settings()
        print_check("Konfiguration", True, f"Provider={settings.llm_provider}")
        return True
    except Exception as error:
        print_check("Konfiguration", False, str(error))
        return False


async def check_logging() -> bool:
    """Prüft ob das Logging funktioniert."""
    try:
        from src.shared.logging_setup import get_logger, setup_logging
        setup_logging("INFO")
        logger = get_logger("verify_m1")
        logger.info("M1 Verifizierung gestartet")
        print_check("Logging", True, "Structlog + Secret-Masking")
        return True
    except Exception as error:
        print_check("Logging", False, str(error))
        return False


async def check_database() -> bool:
    """Prüft ob die Datenbank erstellt und genutzt werden kann."""
    db_path = Path("/tmp/verify_m1_test.db")
    try:
        from src.shared.database import DatabaseManager
        from src.shared.repositories import AuditLogRepository, ScanJobRepository
        from src.shared.types.models import AuditLogEntry, ScanJob

        db = DatabaseManager(db_path)
        await db.initialize()

        # Scan-Job erstellen und lesen
        repo = ScanJobRepository(db)
        job = ScanJob(target="10.10.10.1")
        await repo.create(job)
        loaded = await repo.get_by_id(job.id)
        assert loaded is not None, "Scan-Job konnte nicht geladen werden"
        assert loaded.target == "10.10.10.1", "Scan-Job Target stimmt nicht"

        # Audit-Log schreiben und lesen
        audit = AuditLogRepository(db)
        entry = AuditLogEntry(action="m1.verify", triggered_by="verify_script")
        await audit.create(entry)
        logs = await audit.list_recent(1)
        assert len(logs) == 1, "Audit-Log konnte nicht gelesen werden"

        await db.close()
        db_path.unlink(missing_ok=True)

        print_check("Datenbank", True, "SQLite CRUD + Audit-Log OK")
        return True
    except Exception as error:
        db_path.unlink(missing_ok=True)
        print_check("Datenbank", False, str(error))
        return False


async def check_claude() -> bool:
    """Prüft ob Claude erreichbar ist (Abo-CLI oder API)."""
    try:
        from src.agents.llm_provider import create_llm_provider
        from src.shared.config import get_settings

        settings = get_settings()
        provider = create_llm_provider()
        provider_name = type(provider).__name__

        is_available = await provider.check_availability()

        if is_available:
            print_check(
                "Claude LLM",
                True,
                f"{provider_name} (Provider={settings.llm_provider})",
            )
        else:
            print_check("Claude LLM", False, f"{provider_name} antwortet nicht")
        return is_available
    except Exception as error:
        print_check("Claude LLM", False, str(error))
        return False


async def check_nemoclaw_runtime() -> bool:
    """Prüft ob die NemoClaw-Runtime initialisiert werden kann."""
    try:
        from src.agents.llm_provider import create_llm_provider
        from src.agents.nemoclaw_runtime import NemoClawRuntime

        provider = create_llm_provider()
        runtime = NemoClawRuntime(llm_provider=provider)

        print_check("NemoClaw-Runtime", True, f"Initialisiert mit {type(provider).__name__}")
        return True
    except Exception as error:
        print_check("NemoClaw-Runtime", False, str(error))
        return False


async def check_docker() -> bool:
    """Prüft ob Docker läuft und der Sandbox-Container gebaut ist."""
    try:
        import docker
        client = docker.from_env()

        # Docker-Version prüfen
        version = client.version()
        docker_version = version.get("Version", "unbekannt")

        # Prüfe ob Sandbox-Image existiert
        try:
            client.images.get("sentinelclaw-sandbox:latest")
            has_image = True
        except docker.errors.ImageNotFound:
            has_image = False

        if has_image:
            # Container starten und nmap testen
            container = client.containers.run(
                "sentinelclaw-sandbox:latest",
                command="nmap --version",
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
            )
            nmap_output = container.decode("utf-8").strip().split("\n")[0]
            print_check("Docker + Sandbox", True, f"Docker {docker_version}, {nmap_output}")
            return True
        else:
            print_check(
                "Docker + Sandbox",
                False,
                f"Docker {docker_version} OK, aber Sandbox-Image fehlt. Bitte: docker compose build sandbox",
            )
            return False
    except Exception as error:
        print_check("Docker + Sandbox", False, str(error))
        return False


async def main() -> None:
    """Führt alle M1-Prüfungen durch."""
    print()
    print("=" * 60)
    print("  SentinelClaw — Meilenstein 1 Verifizierung")
    print("=" * 60)
    print()

    results = []
    results.append(await check_config())
    results.append(await check_logging())
    results.append(await check_database())
    results.append(await check_nemoclaw_runtime())
    results.append(await check_claude())
    results.append(await check_docker())

    passed = sum(results)
    total = len(results)

    print()
    print("-" * 60)
    if all(results):
        print(f"  ✅ MEILENSTEIN 1 BESTANDEN ({passed}/{total} Checks)")
    else:
        print(f"  ⚠️  {passed}/{total} Checks bestanden")
        if not results[4]:
            print("  Hinweis: Claude CLI nicht verfügbar oder nicht authentifiziert")
        if not results[5]:
            print("  Hinweis: docker compose build sandbox ausführen")
    print("-" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
