#!/usr/bin/env python3
"""
Meilenstein 4 — Verifizierungs-Script.

Prüft alle FA-01 Akzeptanzkriterien:
1. Agent startet nach Übergabe eines Ziels ohne manuelle Eingriffe
2. Agent erstellt strukturierten Plan mit mindestens 2 Phasen
3. Agent delegiert Ausführung an den Recon-Agenten via MCP
4. Agent liefert nach Abschluss eine strukturierte Zusammenfassung
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shared.logging_setup import setup_logging
setup_logging("WARNING")


def print_check(name: str, passed: bool, detail: str = "") -> None:
    icon = "✅" if passed else "❌"
    suffix = f" — {detail}" if detail else ""
    print(f"  {icon} {name}{suffix}")


async def verify_m4() -> None:
    """Prüft alle FA-01 Akzeptanzkriterien."""
    from src.orchestrator.agent import OrchestratorAgent
    from src.shared.types.scope import PentestScope

    scope = PentestScope(targets_include=["scanme.nmap.org"], max_escalation_level=2)
    orchestrator = OrchestratorAgent(scope=scope)

    print()
    print("=" * 60)
    print("  SentinelClaw — Meilenstein 4 Verifizierung")
    print("  FA-01: Orchestrator-Agent")
    print("=" * 60)
    print()
    print("  Starte orchestrierten Scan auf scanme.nmap.org...")
    print("  (Dies dauert 30-60 Sekunden)")
    print()

    try:
        result = await orchestrator.orchestrate_scan(
            target="scanme.nmap.org",
            scan_type="recon",
            ports="22,80,443",
        )

        # Kriterium 1: Agent startet autonom
        k1 = result.phases_completed > 0
        print_check(
            "FA-01.1: Autonomer Start nach Zielübergabe",
            k1,
            f"{result.phases_completed} Phase(n) gestartet",
        )

        # Kriterium 2: Mindestens 2 Phasen im Plan
        k2 = len(result.plan) >= 2
        print_check(
            "FA-01.2: Strukturierter Plan mit ≥2 Phasen",
            k2,
            f"{len(result.plan)} Phasen: {', '.join(p.name for p in result.plan)}",
        )

        # Kriterium 3: Delegiert an Recon-Agent
        k3 = result.recon_result is not None
        print_check(
            "FA-01.3: Delegation an Recon-Agent",
            k3,
            "Recon-Ergebnis vorhanden" if k3 else "Kein Recon-Ergebnis",
        )

        # Kriterium 4: Strukturierte Zusammenfassung
        k4 = bool(result.executive_summary) and len(result.executive_summary) > 10
        print_check(
            "FA-01.4: Strukturierte Zusammenfassung",
            k4,
            f"{len(result.executive_summary)} Zeichen" if k4 else "Keine Zusammenfassung",
        )

        # Bonus-Checks
        has_ports = result.recon_result and result.recon_result.total_open_ports > 0
        print_check(
            "Bonus: Offene Ports gefunden",
            has_ports,
            f"{result.recon_result.total_open_ports} Ports" if has_ports else "Keine Ports im Parser",
        )

        has_report = bool(result.full_report) and len(result.full_report) > 50
        print_check(
            "Bonus: Vollständiger Report",
            has_report,
            f"{len(result.full_report)} Zeichen" if has_report else "Kein Report",
        )

        print()
        print("-" * 60)
        all_passed = k1 and k2 and k3 and k4
        if all_passed:
            print("  ✅ MEILENSTEIN 4 BESTANDEN (FA-01 erfüllt)")
        else:
            passed = sum([k1, k2, k3, k4])
            print(f"  ⚠️  {passed}/4 Akzeptanzkriterien erfüllt")
        print("-" * 60)

        if result.full_report:
            print()
            print("  --- Agent-Report (Anfang) ---")
            for line in result.full_report[:800].split("\n"):
                print(f"  {line}")

    except Exception as error:
        print(f"\n  ❌ Verifizierung fehlgeschlagen: {error}")

    finally:
        await orchestrator.close()

    print()


if __name__ == "__main__":
    asyncio.run(verify_m4())
