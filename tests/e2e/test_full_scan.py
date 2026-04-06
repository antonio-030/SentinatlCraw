"""
E2E-Test: Vollständiger Scan-Durchlauf.

Testet den kompletten Flow: Orchestrator → Recon-Agent → Sandbox → Ergebnis.
Prüft die Lastenheft-Abnahmekriterien 1-4.

HINWEIS: Dieser Test braucht eine laufende Sandbox (docker compose up -d sandbox)
und eine funktionierende Claude CLI. Er macht einen echten Netzwerk-Scan
auf scanme.nmap.org und dauert 30-120 Sekunden.
"""

from pathlib import Path

import pytest

from src.shared.database import DatabaseManager
from src.shared.repositories import AuditLogRepository, ScanJobRepository
from src.shared.types.models import ScanStatus

TEST_DB = Path("/tmp/test_full_scan_e2e.db")


@pytest.fixture
async def db():
    manager = DatabaseManager(TEST_DB)
    await manager.initialize()
    yield manager
    await manager.close()
    TEST_DB.unlink(missing_ok=True)


async def test_orchestrator_full_scan(db):
    """Lastenheft Kriterien 1-4: Vollständiger orchestrierter Scan."""
    from src.orchestrator.agent import OrchestratorAgent
    from src.shared.types.scope import PentestScope

    scope = PentestScope(targets_include=["scanme.nmap.org"], max_escalation_level=2)
    orchestrator = OrchestratorAgent(scope=scope)

    result = await orchestrator.orchestrate_scan(
        target="scanme.nmap.org",
        scan_type="recon",
        ports="22,80,443",
    )

    # Kriterium 1: Agent startet autonom
    assert result.phases_completed > 0, "Keine Phase abgeschlossen"

    # Kriterium 2: Mindestens 2 Phasen
    assert len(result.plan) >= 2, f"Nur {len(result.plan)} Phase(n) im Plan"

    # Kriterium 3: Recon-Agent wurde delegiert
    assert result.recon_result is not None, "Kein Recon-Ergebnis"

    # Kriterium 4: Strukturierte Zusammenfassung
    assert result.executive_summary, "Keine Executive Summary"
    assert len(result.full_report) > 50, "Report zu kurz"

    await orchestrator.close()


async def test_scan_creates_db_entries(db):
    """Scan erstellt korrekte DB-Einträge (Scan-Job + Audit-Log)."""
    scan_repo = ScanJobRepository(db)
    audit_repo = AuditLogRepository(db)

    from src.shared.types.models import ScanJob

    job = ScanJob(target="10.10.10.1", scan_type="recon")
    await scan_repo.create(job)
    await scan_repo.update_status(job.id, ScanStatus.RUNNING)

    # Prüfe DB-Eintrag
    loaded = await scan_repo.get_by_id(job.id)
    assert loaded is not None
    assert loaded.status == ScanStatus.RUNNING
    assert loaded.started_at is not None

    # Audit-Log schreiben und prüfen
    from src.shared.types.models import AuditLogEntry

    await audit_repo.create(AuditLogEntry(
        action="scan.started",
        resource_type="scan_job",
        resource_id=str(job.id),
        triggered_by="test",
    ))

    logs = await audit_repo.list_by_action("scan.started")
    assert len(logs) >= 1


async def test_scan_result_structured():
    """Scan-Ergebnis ist strukturiert und menschenlesbar (Kriterium 8)."""
    from src.agents.recon.result_types import OpenPort, ReconResult, VulnerabilityFinding

    # Ergebnis-Objekt muss die richtigen Felder haben
    result = ReconResult(
        target="10.10.10.1",
        open_ports=[
            OpenPort(host="10.10.10.1", port=22, service="ssh", version="OpenSSH 8.9"),
            OpenPort(host="10.10.10.1", port=80, service="http", version="nginx 1.24"),
        ],
        vulnerabilities=[
            VulnerabilityFinding(title="Outdated SSH", severity="high", cvss_score=7.5),
        ],
    )

    assert result.total_hosts == 0  # Keine Hosts explizit gesetzt
    assert result.total_open_ports == 2
    assert result.total_vulnerabilities == 1
    assert result.has_critical is False
    assert result.severity_counts == {"high": 1}

    # JSON-Formatierung testen
    import json

    from src.shared.formatters import format_as_json, format_as_markdown

    json_output = format_as_json(result)
    parsed = json.loads(json_output)
    assert "target" in parsed
    assert "open_ports" in parsed

    md_output = format_as_markdown(result)
    assert "10.10.10.1" in md_output
    assert "ssh" in md_output.lower() or "SSH" in md_output


def _sandbox_running() -> bool:
    """Prüft ob der Sandbox-Container läuft."""
    try:
        import docker
        client = docker.from_env()
        container = client.containers.get("sentinelclaw-sandbox")
        return container.status == "running"
    except Exception:
        return False
