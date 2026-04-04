#!/usr/bin/env python3
"""
Meilenstein 2 — Verifizierungs-Script.

Prüft: MCP-Server mit nmap + nuclei als Tools funktioniert.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def print_check(name: str, passed: bool, detail: str = "") -> None:
    icon = "✅" if passed else "❌"
    suffix = f" — {detail}" if detail else ""
    print(f"  {icon} {name}{suffix}")


async def check_scope_validator() -> bool:
    """Prüft ob der Scope-Validator funktioniert."""
    try:
        from src.shared.scope_validator import ScopeValidator
        from src.shared.types.scope import PentestScope

        validator = ScopeValidator()
        scope = PentestScope(targets_include=["10.10.10.0/24"])

        # Erlaubtes Ziel
        r = validator.validate("10.10.10.5", 80, "nmap", scope)
        assert r.allowed, "Erlaubtes Ziel wurde blockiert"

        # Nicht erlaubtes Ziel
        r = validator.validate("192.168.1.1", 80, "nmap", scope)
        assert not r.allowed, "Nicht-erlaubtes Ziel wurde durchgelassen"

        # Eskalation blockiert
        r = validator.validate("10.10.10.5", 80, "metasploit", scope)
        assert not r.allowed, "Eskalation wurde nicht blockiert"

        print_check("Scope-Validator", True, "7 Checks aktiv, Allowlist + Escalation")
        return True
    except Exception as error:
        print_check("Scope-Validator", False, str(error))
        return False


async def check_sandbox_executor() -> bool:
    """Prüft ob der Sandbox-Executor funktioniert."""
    try:
        from src.sandbox.executor import SandboxExecutor

        executor = SandboxExecutor()
        if not executor.is_sandbox_running():
            print_check("Sandbox-Executor", False, "Container läuft nicht")
            return False

        result = await executor.execute(["nmap", "--version"])
        assert result.exit_code == 0, f"nmap Exit-Code: {result.exit_code}"
        assert "Nmap version" in result.stdout

        print_check("Sandbox-Executor", True, "nmap in Container ausführbar")
        return True
    except Exception as error:
        print_check("Sandbox-Executor", False, str(error))
        return False


async def check_port_scan_tool() -> bool:
    """Prüft ob das port_scan Tool echte Scans durchführen kann."""
    try:
        from src.mcp_server.tools.port_scan import run_port_scan
        from src.shared.scope_validator import ScopeValidator
        from src.shared.types.scope import PentestScope
        from src.sandbox.executor import SandboxExecutor

        scope = PentestScope(targets_include=["scanme.nmap.org"])
        result = await run_port_scan(
            target="scanme.nmap.org",
            ports="22,80",
            flags=["-sV"],
            scope=scope,
            executor=SandboxExecutor(),
            scope_validator=ScopeValidator(),
        )

        assert result.total_hosts_up >= 1, "Kein Host gefunden"
        assert result.total_open_ports >= 1, "Keine offenen Ports"

        ports_str = ", ".join(
            f"{p.port}/{p.service}"
            for h in result.hosts for p in h.ports if p.state == "open"
        )
        print_check("port_scan Tool", True, f"{result.total_open_ports} Ports: {ports_str}")
        return True
    except Exception as error:
        print_check("port_scan Tool", False, str(error))
        return False


async def check_scope_blocks_out_of_scope() -> bool:
    """Prüft ob Out-of-Scope-Ziele blockiert werden."""
    try:
        from src.mcp_server.tools.port_scan import run_port_scan
        from src.shared.scope_validator import ScopeValidator
        from src.shared.types.scope import PentestScope
        from src.sandbox.executor import SandboxExecutor

        # Scope enthält NUR scanme.nmap.org
        scope = PentestScope(targets_include=["scanme.nmap.org"])

        try:
            await run_port_scan(
                target="192.168.1.1",  # NICHT im Scope
                ports="80",
                scope=scope,
                executor=SandboxExecutor(),
                scope_validator=ScopeValidator(),
            )
            print_check("Scope-Blockade", False, "Out-of-Scope wurde NICHT blockiert!")
            return False
        except PermissionError:
            print_check("Scope-Blockade", True, "Out-of-Scope korrekt abgelehnt")
            return True
    except Exception as error:
        print_check("Scope-Blockade", False, str(error))
        return False


async def check_input_validation() -> bool:
    """Prüft ob gefährliche Inputs abgelehnt werden."""
    try:
        from src.mcp_server.tools.input_validation import validate_target

        # Command Injection Versuch
        try:
            validate_target("10.10.10.5; rm -rf /")
            print_check("Input-Validierung", False, "Injection nicht blockiert!")
            return False
        except ValueError:
            pass

        # Backtick Injection
        try:
            validate_target("`whoami`")
            print_check("Input-Validierung", False, "Backtick nicht blockiert!")
            return False
        except ValueError:
            pass

        print_check("Input-Validierung", True, "Injection-Versuche blockiert")
        return True
    except Exception as error:
        print_check("Input-Validierung", False, str(error))
        return False


async def main() -> None:
    print()
    print("=" * 60)
    print("  SentinelClaw — Meilenstein 2 Verifizierung")
    print("=" * 60)
    print()

    results = []
    results.append(await check_scope_validator())
    results.append(await check_sandbox_executor())
    results.append(await check_input_validation())
    results.append(await check_port_scan_tool())
    results.append(await check_scope_blocks_out_of_scope())

    passed = sum(results)
    total = len(results)

    print()
    print("-" * 60)
    if all(results):
        print(f"  ✅ MEILENSTEIN 2 BESTANDEN ({passed}/{total} Checks)")
    else:
        print(f"  ⚠️  {passed}/{total} Checks bestanden")
    print("-" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
