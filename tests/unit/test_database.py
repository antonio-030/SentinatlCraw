"""Unit-Tests für die Datenbank und Repositories."""

import asyncio
from pathlib import Path
from uuid import uuid4

import pytest

from src.shared.database import DatabaseManager
from src.shared.repositories import (
    AgentLogRepository,
    AuditLogRepository,
    FindingRepository,
    ScanJobRepository,
)
from src.shared.types.models import (
    AgentLogEntry,
    AuditLogEntry,
    Finding,
    ScanJob,
    ScanStatus,
    Severity,
)

TEST_DB_PATH = Path("/tmp/test_sentinelclaw_unit.db")


@pytest.fixture
async def db():
    """Erstellt eine frische Test-Datenbank für jeden Test."""
    manager = DatabaseManager(TEST_DB_PATH)
    await manager.initialize()
    yield manager
    await manager.close()
    TEST_DB_PATH.unlink(missing_ok=True)


@pytest.fixture
def scan_job_repo(db):
    return ScanJobRepository(db)


@pytest.fixture
def finding_repo(db):
    return FindingRepository(db)


@pytest.fixture
def audit_repo(db):
    return AuditLogRepository(db)


@pytest.fixture
def agent_log_repo(db):
    return AgentLogRepository(db)


async def test_scan_job_create_and_read(scan_job_repo):
    """Scan-Job erstellen und zurücklesen."""
    job = ScanJob(target="10.10.10.0/24", scan_type="recon")
    created = await scan_job_repo.create(job)
    loaded = await scan_job_repo.get_by_id(created.id)

    assert loaded is not None
    assert loaded.target == "10.10.10.0/24"
    assert loaded.status == ScanStatus.PENDING


async def test_scan_job_status_update(scan_job_repo):
    """Scan-Job Status aktualisieren."""
    job = ScanJob(target="10.10.10.5")
    await scan_job_repo.create(job)

    await scan_job_repo.update_status(job.id, ScanStatus.RUNNING)
    loaded = await scan_job_repo.get_by_id(job.id)
    assert loaded.status == ScanStatus.RUNNING
    assert loaded.started_at is not None

    await scan_job_repo.update_status(job.id, ScanStatus.COMPLETED, tokens_used=25000)
    loaded = await scan_job_repo.get_by_id(job.id)
    assert loaded.status == ScanStatus.COMPLETED
    assert loaded.completed_at is not None
    assert loaded.tokens_used == 25000


async def test_scan_job_emergency_kill(scan_job_repo):
    """Scan-Job auf EMERGENCY_KILLED setzen."""
    job = ScanJob(target="10.10.10.1")
    await scan_job_repo.create(job)
    await scan_job_repo.update_status(job.id, ScanStatus.RUNNING)
    await scan_job_repo.update_status(job.id, ScanStatus.EMERGENCY_KILLED)

    loaded = await scan_job_repo.get_by_id(job.id)
    assert loaded.status == ScanStatus.EMERGENCY_KILLED


async def test_scan_job_list_by_status(scan_job_repo):
    """Scan-Jobs nach Status filtern."""
    await scan_job_repo.create(ScanJob(target="10.10.10.1"))
    job2 = ScanJob(target="10.10.10.2")
    await scan_job_repo.create(job2)
    await scan_job_repo.update_status(job2.id, ScanStatus.RUNNING)

    running = await scan_job_repo.list_by_status(ScanStatus.RUNNING)
    assert len(running) == 1
    assert running[0].target == "10.10.10.2"


async def test_finding_create_and_list(finding_repo, scan_job_repo):
    """Finding erstellen und nach Scan auflisten."""
    job = ScanJob(target="10.10.10.5")
    await scan_job_repo.create(job)

    finding = Finding(
        scan_job_id=job.id,
        tool_name="nuclei",
        title="SQL Injection in Login",
        severity=Severity.CRITICAL,
        cvss_score=9.1,
        cve_id="CVE-2024-1234",
        target_host="10.10.10.5",
        target_port=3306,
        service="mysql",
        description="Login-Formular anfällig für SQL Injection",
    )
    await finding_repo.create(finding)

    findings = await finding_repo.list_by_scan(job.id)
    assert len(findings) == 1
    assert findings[0].title == "SQL Injection in Login"
    assert findings[0].severity == Severity.CRITICAL
    assert findings[0].cvss_score == 9.1


async def test_audit_log_immutable(audit_repo):
    """Audit-Log hat kein update und kein delete — nur create und list."""
    entry = AuditLogEntry(
        action="scan.started",
        resource_type="scan_job",
        resource_id="test-123",
        details={"target": "10.10.10.1"},
        triggered_by="test_user",
    )
    await audit_repo.create(entry)

    logs = await audit_repo.list_recent(10)
    assert len(logs) == 1
    assert logs[0].action == "scan.started"
    assert logs[0].triggered_by == "test_user"

    # Prüfe dass AuditLogRepository KEINE update/delete Methoden hat
    assert not hasattr(audit_repo, "update"), "AuditLog darf kein update() haben"
    assert not hasattr(audit_repo, "delete"), "AuditLog darf kein delete() haben"


async def test_audit_log_filter_by_action(audit_repo):
    """Audit-Log nach Aktion filtern."""
    await audit_repo.create(AuditLogEntry(action="scan.started"))
    await audit_repo.create(AuditLogEntry(action="scan.completed"))
    await audit_repo.create(AuditLogEntry(action="scan.started"))

    started = await audit_repo.list_by_action("scan.started")
    assert len(started) == 2

    completed = await audit_repo.list_by_action("scan.completed")
    assert len(completed) == 1


async def test_agent_log_create_and_list(agent_log_repo, scan_job_repo):
    """Agent-Log-Einträge erstellen und nach Scan auflisten."""
    job = ScanJob(target="10.10.10.5")
    await scan_job_repo.create(job)

    entry = AgentLogEntry(
        scan_job_id=job.id,
        agent_name="recon-agent",
        step_description="Port-Scan gestartet",
        tool_name="nmap",
        input_params={"target": "10.10.10.5", "ports": "1-1000"},
        output_summary="5 offene Ports gefunden",
        duration_ms=45000,
    )
    await agent_log_repo.create(entry)

    logs = await agent_log_repo.list_by_scan(job.id)
    assert len(logs) == 1
    assert logs[0].agent_name == "recon-agent"
    assert logs[0].tool_name == "nmap"
    assert logs[0].duration_ms == 45000
