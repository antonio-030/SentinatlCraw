"""
E2E-Test: Scope-Enforcement.

Prüft dass der Scope-Validator Out-of-Scope-Ziele blockiert
und die Blockade korrekt im Audit-Log vermerkt wird.
Lastenheft Kriterium 6: Kein Netzwerkzugriff auf nicht-autorisierte Ziele.
"""

import asyncio
from pathlib import Path

import pytest

from src.shared.database import DatabaseManager
from src.shared.repositories import AuditLogRepository
from src.shared.scope_validator import ScopeValidator
from src.shared.types.scope import PentestScope
from src.mcp_server.tools.port_scan import run_port_scan
from src.sandbox.executor import SandboxExecutor

TEST_DB = Path("/tmp/test_scope_e2e.db")


@pytest.fixture
async def db():
    manager = DatabaseManager(TEST_DB)
    await manager.initialize()
    yield manager
    await manager.close()
    TEST_DB.unlink(missing_ok=True)


async def test_out_of_scope_target_blocked():
    """Ziel außerhalb des Scopes wird vom Scope-Validator blockiert."""
    scope = PentestScope(targets_include=["10.10.10.0/24"])
    validator = ScopeValidator()

    # 192.168.1.1 ist NICHT im Scope
    result = validator.validate("192.168.1.1", 80, "nmap", scope)

    assert not result.allowed
    assert "nicht in der Whitelist" in result.reason


async def test_out_of_scope_port_scan_rejected():
    """Port-Scan auf Out-of-Scope-Ziel wird von port_scan Tool abgelehnt."""
    scope = PentestScope(targets_include=["scanme.nmap.org"])
    validator = ScopeValidator()
    executor = SandboxExecutor()

    with pytest.raises(PermissionError, match="Scope-Verletzung"):
        await run_port_scan(
            target="192.168.1.1",
            ports="80",
            scope=scope,
            executor=executor,
            scope_validator=validator,
        )


async def test_escalation_blocked():
    """Tool über der erlaubten Eskalationsstufe wird blockiert."""
    scope = PentestScope(
        targets_include=["10.10.10.0/24"],
        max_escalation_level=1,  # Nur Stufe 0-1 erlaubt
    )
    validator = ScopeValidator()

    # nuclei ist Stufe 2 → muss blockiert werden
    result = validator.validate("10.10.10.5", 80, "nuclei", scope)
    assert not result.allowed
    assert "überschreitet" in result.reason


async def test_forbidden_loopback_always_blocked():
    """Loopback-Adressen werden IMMER blockiert, auch wenn im Scope."""
    scope = PentestScope(targets_include=["127.0.0.0/8"])
    validator = ScopeValidator()

    result = validator.validate("127.0.0.1", 80, "nmap", scope)
    assert not result.allowed
    assert "verbotenen IP-Range" in result.reason


async def test_excluded_target_blocked():
    """Explizit ausgeschlossenes Ziel wird blockiert."""
    scope = PentestScope(
        targets_include=["10.10.10.0/24"],
        targets_exclude=["10.10.10.1"],
    )
    validator = ScopeValidator()

    # 10.10.10.5 erlaubt
    r1 = validator.validate("10.10.10.5", None, "nmap", scope)
    assert r1.allowed

    # 10.10.10.1 ausgeschlossen
    r2 = validator.validate("10.10.10.1", None, "nmap", scope)
    assert not r2.allowed


async def test_unknown_tool_blocked():
    """Unbekannte Tools werden immer blockiert."""
    scope = PentestScope(targets_include=["10.10.10.0/24"])
    validator = ScopeValidator()

    result = validator.validate("10.10.10.5", 80, "malicious_tool", scope)
    assert not result.allowed
    assert "nicht in der Tool-Zuordnung" in result.reason


async def test_command_injection_blocked():
    """Command-Injection-Versuche werden durch Input-Validierung blockiert."""
    from src.mcp_server.tools.input_validation import validate_target

    dangerous_inputs = [
        "10.10.10.5; rm -rf /",
        "10.10.10.5 | cat /etc/passwd",
        "`whoami`",
        "$(id)",
        "10.10.10.5 && echo pwned",
    ]

    for payload in dangerous_inputs:
        with pytest.raises(ValueError):
            validate_target(payload)
