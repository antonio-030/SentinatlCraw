"""
SentinelClaw CLI — Kommandozeilen-Interface für den PoC.

Starten mit: python -m src.cli scan --target <IP/CIDR>
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from uuid import UUID

from src.shared.config import get_settings
from src.shared.database import DatabaseManager
from src.shared.exporters import export_findings_csv, export_findings_jsonl, export_findings_sarif
from src.shared.logging_setup import get_logger, setup_logging
from src.shared.repositories import AuditLogRepository, FindingRepository, ScanJobRepository
from src.shared.scope_validator import ScopeValidator
from src.shared.types.models import AuditLogEntry, ScanJob, ScanStatus, Severity
from src.shared.types.scope import PentestScope

logger = get_logger(__name__)


async def cmd_scan(args: argparse.Namespace) -> None:
    """Führt einen Recon-Scan auf dem Ziel durch."""
    settings = get_settings()
    target = args.target

    # Scope aus Konfiguration + CLI-Target bauen
    allowed = settings.get_allowed_targets_list()
    if target not in allowed and not any(target in a for a in allowed):
        # Target automatisch zur erlaubten Liste hinzufügen (PoC)
        allowed.append(target)

    scope = PentestScope(
        targets_include=allowed,
        max_escalation_level=min(args.level, 2),
        ports_include=args.ports,
    )

    # Disclaimer anzeigen
    print()
    print("=" * 60)
    print("  ⚠  RECHTLICHER HINWEIS")
    print("=" * 60)
    print()
    print("  Dieses Tool darf ausschließlich für autorisierte")
    print("  Sicherheitsüberprüfungen eingesetzt werden.")
    print("  (StGB §202a-c)")
    print()

    if not args.yes:
        confirm = input("  Autorisierung bestätigen? [j/N]: ").strip().lower()
        if confirm not in ("j", "ja", "y", "yes"):
            print("  Abgebrochen.")
            return

    print()
    print(f"  Ziel:  {target}")
    print(f"  Ports: {args.ports}")
    print(f"  Stufe: {args.level}")
    print()

    # DB initialisieren
    db = DatabaseManager(settings.db_path)
    await db.initialize()
    scan_repo = ScanJobRepository(db)
    audit_repo = AuditLogRepository(db)

    # Scan-Job erstellen
    job = ScanJob(
        target=target,
        scan_type="recon",
        max_escalation_level=args.level,
        token_budget=settings.llm_max_tokens_per_scan,
        config={"ports": args.ports},
    )
    await scan_repo.create(job)
    await scan_repo.update_status(job.id, ScanStatus.RUNNING)

    # Audit-Log
    await audit_repo.create(AuditLogEntry(
        action="scan.started",
        resource_type="scan_job",
        resource_id=str(job.id),
        details={"target": target, "level": args.level},
        triggered_by="cli_user",
    ))

    print(f"  Scan-ID: {job.id}")
    print(f"  Status:  RUNNING")
    print()

    # NemoClaw-Runtime und Recon-Agent erstellen
    from src.agents.nemoclaw_runtime import NemoClawRuntime
    from src.agents.recon.agent import ReconAgent

    runtime = NemoClawRuntime()
    agent = ReconAgent(runtime=runtime, scope=scope)

    print("  Agent arbeitet...")
    print()

    start_time = time.monotonic()

    try:
        result = await agent.run_reconnaissance(target, ports=args.ports)

        duration = time.monotonic() - start_time
        await scan_repo.update_status(
            job.id, ScanStatus.COMPLETED, tokens_used=result.total_tokens_used
        )

        # Ergebnis ausgeben
        _print_result(result, args.output)

        # Audit-Log
        await audit_repo.create(AuditLogEntry(
            action="scan.completed",
            resource_type="scan_job",
            resource_id=str(job.id),
            details={
                "hosts": result.total_hosts,
                "ports": result.total_open_ports,
                "vulns": result.total_vulnerabilities,
                "duration_s": round(duration, 1),
                "tokens": result.total_tokens_used,
            },
            triggered_by="cli_user",
        ))

    except Exception as error:
        await scan_repo.update_status(job.id, ScanStatus.FAILED)
        logger.error("Scan fehlgeschlagen", error=str(error), scan_id=str(job.id))
        print(f"\n  ❌ Scan fehlgeschlagen: {error}")

    finally:
        await db.close()


def _print_result(result, output_format: str) -> None:
    """Gibt das Scan-Ergebnis formatiert aus."""
    if output_format == "json":
        data = {
            "target": result.target,
            "hosts": [{"address": h.address, "hostname": h.hostname} for h in result.discovered_hosts],
            "open_ports": [
                {"host": p.host, "port": p.port, "service": p.service, "version": p.version}
                for p in result.open_ports
            ],
            "vulnerabilities": [
                {"title": v.title, "severity": v.severity, "cvss": v.cvss_score, "cve": v.cve_id, "host": v.host}
                for v in result.vulnerabilities
            ],
            "summary": {
                "total_hosts": result.total_hosts,
                "total_open_ports": result.total_open_ports,
                "total_vulnerabilities": result.total_vulnerabilities,
                "severity_counts": result.severity_counts,
                "duration_seconds": round(result.scan_duration_seconds, 1),
                "tokens_used": result.total_tokens_used,
            },
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    # Markdown-Ausgabe
    print("=" * 60)
    print(f"  SCAN-ERGEBNIS: {result.target}")
    print("=" * 60)
    print()
    print(f"  Hosts:           {result.total_hosts}")
    print(f"  Offene Ports:    {result.total_open_ports}")
    print(f"  Vulnerabilities: {result.total_vulnerabilities}")
    print(f"  Dauer:           {result.scan_duration_seconds:.1f}s")
    print(f"  Tokens:          {result.total_tokens_used}")
    print()

    if result.open_ports:
        print("  --- Offene Ports ---")
        for p in result.open_ports:
            print(f"  {p.host}:{p.port}/{p.protocol}  {p.service}  {p.version}")
        print()

    if result.vulnerabilities:
        print("  --- Vulnerabilities ---")
        severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}
        for v in sorted(result.vulnerabilities, key=lambda x: x.cvss_score, reverse=True):
            icon = severity_icons.get(v.severity.lower(), "⚪")
            cve = f" ({v.cve_id})" if v.cve_id else ""
            print(f"  {icon} {v.severity.upper():8s} {v.title}{cve}")
            if v.host:
                print(f"                    {v.host}:{v.port or '?'}")
        print()

    if result.agent_summary:
        print("  --- Agent-Zusammenfassung ---")
        # Nur die ersten 1000 Zeichen des Agent-Outputs
        summary = result.agent_summary[:1000]
        for line in summary.split("\n"):
            print(f"  {line}")
        print()

    if result.errors:
        print("  --- Fehler ---")
        for err in result.errors:
            print(f"  ⚠ {err}")
        print()


def main() -> None:
    """CLI-Einstiegspunkt."""
    parser = argparse.ArgumentParser(
        prog="sentinelclaw",
        description="SentinelClaw — AI-gestützte Security Assessment Platform",
    )
    subparsers = parser.add_subparsers(dest="command")

    # Scan-Command
    scan_parser = subparsers.add_parser("scan", help="Recon-Scan durchführen")
    scan_parser.add_argument("--target", "-t", required=True, help="Scan-Ziel (IP, CIDR, Domain)")
    scan_parser.add_argument("--ports", "-p", default="1-1000", help="Port-Range (Default: 1-1000)")
    scan_parser.add_argument("--level", "-l", type=int, default=2, choices=[0, 1, 2], help="Eskalationsstufe (0-2)")
    scan_parser.add_argument("--output", "-o", default="markdown", choices=["markdown", "json"], help="Ausgabeformat")
    scan_parser.add_argument("--yes", "-y", action="store_true", help="Disclaimer automatisch bestätigen")

    # Orchestrate-Command (FA-01)
    orch_parser = subparsers.add_parser("orchestrate", help="Orchestrierten Scan durchführen")
    orch_parser.add_argument("--target", "-t", required=True, help="Scan-Ziel")
    orch_parser.add_argument("--ports", "-p", default="1-1000", help="Port-Range")
    orch_parser.add_argument("--profile", choices=["quick", "standard", "full", "web", "database", "infrastructure", "stealth"], help="Scan-Profil (überschreibt --ports)")
    orch_parser.add_argument("--type", default="recon", choices=["recon", "vuln", "full"], help="Scan-Typ")
    orch_parser.add_argument("--output", "-o", default="markdown", choices=["markdown", "json"], help="Ausgabeformat")
    orch_parser.add_argument("--yes", "-y", action="store_true", help="Disclaimer bestätigen")

    # Profiles-Command
    subparsers.add_parser("profiles", help="Verfügbare Scan-Profile anzeigen")

    # Status-Command
    subparsers.add_parser("status", help="System-Status und laufende Scans anzeigen")

    # History-Command
    hist_parser = subparsers.add_parser("history", help="Vergangene Scans anzeigen")
    hist_parser.add_argument("--limit", "-n", type=int, default=10, help="Anzahl Einträge")

    # Kill-Command
    subparsers.add_parser("kill", help="Alle laufenden Scans sofort stoppen (NOTAUS)")

    # Findings-Command
    find_parser = subparsers.add_parser("findings", help="Findings anzeigen und exportieren")
    find_parser.add_argument(
        "--severity", "-s",
        choices=["critical", "high", "medium", "low", "info"],
    )
    find_parser.add_argument("--scan-id", help="Nur Findings eines bestimmten Scans")
    find_parser.add_argument("--host", help="Nur Findings eines bestimmten Hosts")
    find_parser.add_argument(
        "--output", "-o", default="table", choices=["table", "json"],
    )
    find_parser.add_argument("--limit", "-n", type=int, default=50)

    # Compare-Command — Scan-Vergleich
    cmp_parser = subparsers.add_parser("compare", help="Zwei Scans vergleichen (Delta)")
    cmp_parser.add_argument("--scan-a", required=True, help="Scan-ID A (Baseline)")
    cmp_parser.add_argument("--scan-b", required=True, help="Scan-ID B (Neuer Scan)")
    cmp_parser.add_argument(
        "--output", "-o", default="table", choices=["table", "json"],
        help="Ausgabeformat",
    )

    # Report-Command
    report_parser = subparsers.add_parser("report", help="Report generieren")
    report_parser.add_argument("--scan-id", required=True, help="Scan-ID")
    report_parser.add_argument(
        "--type", default="technical",
        choices=["executive", "technical", "compliance"],
    )
    report_parser.add_argument("--output-file", "-f", help="In Datei schreiben")

    # Export-Command — Findings in verschiedenen Formaten exportieren
    export_parser = subparsers.add_parser("export", help="Findings exportieren (CSV, JSONL, SARIF)")
    export_parser.add_argument("--scan-id", required=True, help="Scan-ID fuer den Export")
    export_parser.add_argument(
        "--format",
        required=True,
        choices=["csv", "jsonl", "sarif"],
        help="Exportformat: csv, jsonl oder sarif",
    )
    export_parser.add_argument("--output-file", "-f", help="In Datei schreiben (sonst stdout)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Logging initialisieren
    settings = get_settings()
    setup_logging(settings.log_level)

    if args.command == "scan":
        asyncio.run(cmd_scan(args))
    elif args.command == "orchestrate":
        asyncio.run(cmd_orchestrate(args))
    elif args.command == "status":
        asyncio.run(cmd_status())
    elif args.command == "history":
        asyncio.run(cmd_history(args))
    elif args.command == "kill":
        asyncio.run(cmd_kill())
    elif args.command == "findings":
        asyncio.run(cmd_findings(args))
    elif args.command == "compare":
        asyncio.run(cmd_compare(args))
    elif args.command == "report":
        asyncio.run(cmd_report(args))
    elif args.command == "export":
        asyncio.run(cmd_export(args))
    elif args.command == "profiles":
        cmd_profiles()


def cmd_profiles() -> None:
    """Zeigt alle verfügbaren Scan-Profile an."""
    from src.shared.scan_profiles import list_profiles

    print()
    print("  SentinelClaw — Scan-Profile")
    print("  " + "=" * 55)
    print()
    for profile in list_profiles():
        print(f"  {profile.name}")
        print(f"    {profile.description}")
        print(f"    Ports: {profile.ports}")
        print(f"    Stufe: {profile.max_escalation_level} | ~{profile.estimated_duration_minutes} Min")
        print()
    print("  Nutzung: sentinelclaw orchestrate --target <ziel> --profile <name>")
    print()


async def cmd_orchestrate(args: argparse.Namespace) -> None:
    """Führt einen orchestrierten Scan durch (FA-01)."""
    settings = get_settings()
    target = args.target

    # Profil laden (überschreibt Ports und Eskalationsstufe)
    ports = args.ports
    escalation = 2
    profile_name = ""

    if hasattr(args, "profile") and args.profile:
        from src.shared.scan_profiles import get_profile
        profile = get_profile(args.profile)
        ports = profile.ports
        escalation = profile.max_escalation_level
        profile_name = profile.name

    # Scope bauen
    allowed = settings.get_allowed_targets_list()
    if target not in allowed:
        allowed.append(target)

    scope = PentestScope(
        targets_include=allowed,
        max_escalation_level=escalation,
        ports_include=ports,
    )

    # Disclaimer
    print()
    print("=" * 60)
    print("  SentinelClaw — Orchestrierter Security-Scan")
    print("  Powered by NVIDIA NemoClaw")
    print("=" * 60)
    print()
    print(f"  Ziel:     {target}")
    print(f"  Ports:    {ports}")
    if profile_name:
        print(f"  Profil:   {profile_name}")
    print(f"  Typ:      {args.type}")
    print()
    print("  ⚠  Dieses Tool darf ausschließlich für autorisierte")
    print("     Sicherheitsüberprüfungen eingesetzt werden. (StGB §202a-c)")
    print()

    if not args.yes:
        confirm = input("  Autorisierung bestätigen? [j/N]: ").strip().lower()
        if confirm not in ("j", "ja", "y", "yes"):
            print("  Abgebrochen.")
            return

    print()
    print("  Orchestrator erstellt Scan-Plan...")
    print()

    from src.orchestrator.agent import OrchestratorAgent

    orchestrator = OrchestratorAgent(scope=scope)

    try:
        result = await orchestrator.orchestrate_scan(
            target=target,
            scan_type=args.type,
            ports=args.ports,
        )

        # Scan-Plan anzeigen
        print("  Scan-Plan:")
        for i, phase in enumerate(result.plan, 1):
            icon = "✅" if phase.status == "completed" else "❌" if phase.status == "failed" else "⏳"
            print(f"    {icon} Phase {i}: {phase.name}")
        print()

        if result.recon_result:
            _print_result(result.recon_result, args.output)

        # Executive Summary
        if result.executive_summary:
            print("  --- Executive Summary ---")
            print(f"  {result.executive_summary}")
            print()

        # Empfehlungen
        if result.recommendations:
            print("  --- Empfehlungen ---")
            for rec in result.recommendations:
                print(f"    → {rec}")
            print()

        print(f"  Dauer:  {result.total_duration_seconds:.1f}s")
        print(f"  Tokens: {result.total_tokens_used}")
        print()

    except Exception as error:
        print(f"\n  ❌ Scan fehlgeschlagen: {error}")

    finally:
        await orchestrator.close()


async def cmd_status() -> None:
    """Zeigt System-Status und laufende Scans."""
    settings = get_settings()
    print()
    print("  SentinelClaw — System-Status")
    print("  " + "=" * 40)
    print()

    # LLM-Provider
    print(f"  LLM-Provider:    {settings.llm_provider}")

    # Claude CLI prüfen
    import shutil
    claude_path = shutil.which("claude")
    print(f"  Claude CLI:      {'✅ ' + claude_path if claude_path else '❌ Nicht gefunden'}")

    # Docker prüfen
    try:
        import docker
        client = docker.from_env()
        version = client.version().get("Version", "?")
        print(f"  Docker:          ✅ {version}")

        try:
            sandbox = client.containers.get("sentinelclaw-sandbox")
            print(f"  Sandbox:         ✅ {sandbox.status}")
        except docker.errors.NotFound:
            print("  Sandbox:         ❌ Container nicht gestartet")
    except Exception:
        print("  Docker:          ❌ Nicht erreichbar")

    # OpenClaw prüfen
    try:
        from openclaw import OpenClaw
        print("  OpenClaw/NemoClaw: ✅ SDK verfügbar")
    except Exception:
        print("  OpenClaw/NemoClaw: ⚠ SDK nicht importierbar")

    # DB prüfen
    db = DatabaseManager(settings.db_path)
    try:
        await db.initialize()
        scan_repo = ScanJobRepository(db)
        running = await scan_repo.list_by_status(ScanStatus.RUNNING)
        all_scans = await scan_repo.list_all(5)

        print(f"  Datenbank:       ✅ {settings.db_path}")
        print(f"  Laufende Scans:  {len(running)}")
        print(f"  Gesamt-Scans:    {len(all_scans)}")

        if running:
            print()
            print("  --- Laufende Scans ---")
            for job in running:
                print(f"    {job.id} → {job.target} ({job.scan_type}, seit {job.started_at})")

        await db.close()
    except Exception as error:
        print(f"  Datenbank:       ❌ {error}")

    print()


async def cmd_history(args) -> None:
    """Zeigt vergangene Scans."""
    settings = get_settings()
    db = DatabaseManager(settings.db_path)
    await db.initialize()
    scan_repo = ScanJobRepository(db)

    scans = await scan_repo.list_all(args.limit)

    print()
    print("  SentinelClaw — Scan-Historie")
    print("  " + "=" * 55)
    print()

    if not scans:
        print("  Noch keine Scans durchgeführt.")
    else:
        status_icons = {
            "completed": "✅",
            "failed": "❌",
            "running": "🔵",
            "pending": "⏳",
            "cancelled": "⚪",
            "emergency_killed": "🔴",
        }
        print(f"  {'Status':<4} {'ID':<10} {'Ziel':<25} {'Typ':<8} {'Tokens':>8} {'Datum'}")
        print(f"  {'─' * 70}")
        for job in scans:
            icon = status_icons.get(job.status.value, "?")
            scan_id = str(job.id)[:8]
            date = job.created_at.strftime("%d.%m.%Y %H:%M")
            print(f"  {icon}    {scan_id:<10} {job.target:<25} {job.scan_type:<8} {job.tokens_used:>8} {date}")

    await db.close()
    print()


async def cmd_kill() -> None:
    """Aktiviert den Kill-Switch — stoppt ALLE laufenden Scans."""
    from src.shared.kill_switch import KillSwitch

    print()
    print("  🔴 SentinelClaw — NOTAUS")
    print("  " + "=" * 40)
    print()

    confirm = input("  Wirklich ALLE Scans sofort stoppen? [j/N]: ").strip().lower()
    if confirm not in ("j", "ja", "y", "yes"):
        print("  Abgebrochen.")
        return

    ks = KillSwitch()
    ks.activate(triggered_by="cli_user", reason="Manueller Kill über CLI")

    print()
    print("  ✅ Kill-Switch aktiviert")
    print("  ✅ Sandbox-Container wird gestoppt")
    print("  ✅ Alle laufenden Scans abgebrochen")
    print()

    # Laufende Scans in DB auf KILLED setzen
    settings = get_settings()
    db = DatabaseManager(settings.db_path)
    try:
        await db.initialize()
        scan_repo = ScanJobRepository(db)
        running = await scan_repo.list_by_status(ScanStatus.RUNNING)
        for job in running:
            await scan_repo.update_status(job.id, ScanStatus.EMERGENCY_KILLED)
            print(f"  Scan {str(job.id)[:8]} → EMERGENCY_KILLED")

        # Audit-Log
        audit_repo = AuditLogRepository(db)
        await audit_repo.create(AuditLogEntry(
            action="kill.activated",
            resource_type="system",
            details={"scans_killed": len(running)},
            triggered_by="cli_user",
        ))
        await db.close()
    except Exception:
        pass

    print()


async def cmd_findings(args: argparse.Namespace) -> None:
    """Listet Findings aus der Datenbank, sortiert nach Schweregrad."""
    settings = get_settings()
    db = DatabaseManager(settings.db_path)
    await db.initialize()
    finding_repo = FindingRepository(db)

    # Findings laden — je nach Filter-Kombination
    if args.scan_id:
        findings = await finding_repo.list_by_scan(UUID(args.scan_id))
    else:
        findings = await finding_repo.list_all(
            severity=args.severity, limit=args.limit,
        )

    # Nachfilter: Host-Filter wird in-memory angewendet
    if args.host:
        findings = [f for f in findings if f.target_host == args.host]

    # Severity-Filter auch bei scan-id-Abfrage anwenden
    if args.severity and args.scan_id:
        findings = [f for f in findings if f.severity.value == args.severity]

    await db.close()

    if args.output == "json":
        _print_findings_json(findings)
    else:
        _print_findings_table(findings)


def _print_findings_json(findings: list) -> None:
    """Gibt Findings als JSON aus."""
    data = [
        {
            "id": str(f.id),
            "scan_job_id": str(f.scan_job_id),
            "title": f.title,
            "severity": f.severity.value,
            "cvss_score": f.cvss_score,
            "cve_id": f.cve_id,
            "host": f.target_host,
            "port": f.target_port,
            "service": f.service,
            "description": f.description,
            "recommendation": f.recommendation,
            "created_at": f.created_at.isoformat(),
        }
        for f in findings
    ]
    print(json.dumps(data, indent=2, ensure_ascii=False))


def _print_findings_table(findings: list) -> None:
    """Gibt Findings als formatierte Tabelle aus."""
    severity_icons: dict[str, str] = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
        "info": "⚪",
    }

    print()
    print("  SentinelClaw — Findings")
    print("  " + "=" * 75)
    print()

    if not findings:
        print("  Keine Findings gefunden.")
        print()
        return

    # Tabellenkopf
    print(
        f"  {'Severity':<12} {'Title':<30} {'Host:Port':<22} "
        f"{'CVE':<16} {'CVSS':>5}"
    )
    print(f"  {'─' * 85}")

    for finding in findings:
        icon = severity_icons.get(finding.severity.value, "⚪")
        sev_label = f"{icon} {finding.severity.value.upper()}"
        title = finding.title[:28] + ".." if len(finding.title) > 30 else finding.title
        port_str = str(finding.target_port) if finding.target_port else "—"
        host_port = f"{finding.target_host}:{port_str}"
        cve = finding.cve_id or "—"
        cvss = f"{finding.cvss_score:.1f}"
        print(f"  {sev_label:<14} {title:<30} {host_port:<22} {cve:<16} {cvss:>5}")

    print()
    print(f"  Gesamt: {len(findings)} Findings")
    print()


async def cmd_report(args: argparse.Namespace) -> None:
    """Generiert einen Report für einen bestimmten Scan."""
    from src.shared.report_generator import ReportGenerator

    settings = get_settings()
    db = DatabaseManager(settings.db_path)
    await db.initialize()

    generator = ReportGenerator(db)
    scan_id = UUID(args.scan_id)
    report_type = args.type

    # Report-Typ auswählen und generieren
    if report_type == "executive":
        content = await generator.generate_executive_summary(scan_id)
    elif report_type == "compliance":
        content = await generator.generate_compliance_report(scan_id)
    else:
        content = await generator.generate_technical_report(scan_id)

    await db.close()

    # Ausgabe: in Datei oder auf stdout
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.write_text(content, encoding="utf-8")
        print(f"\n  ✅ Report geschrieben: {output_path.resolve()}\n")
    else:
        print(content)


async def cmd_export(args: argparse.Namespace) -> None:
    """Exportiert Findings eines Scans in das gewaehlte Format (CSV, JSONL, SARIF)."""
    settings = get_settings()
    db = DatabaseManager(settings.db_path)
    await db.initialize()

    scan_id = UUID(args.scan_id)
    fmt: str = args.format

    # Passendes Exportformat waehlen
    exporters: dict[str, any] = {
        "csv": export_findings_csv,
        "jsonl": export_findings_jsonl,
        "sarif": export_findings_sarif,
    }

    exporter = exporters[fmt]
    content: str = await exporter(db, scan_id)
    await db.close()

    # Ausgabe: in Datei oder auf stdout
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.write_text(content, encoding="utf-8")
        print(f"\n  Exportiert: {output_path.resolve()}  ({fmt.upper()})\n")
    else:
        print(content)


async def cmd_compare(args: argparse.Namespace) -> None:
    """Vergleicht zwei Scans und zeigt das Delta (neue/behobene Findings, Ports)."""
    from src.shared.scan_compare import ScanComparator

    settings = get_settings()
    db = DatabaseManager(settings.db_path)
    await db.initialize()

    scan_id_a = UUID(args.scan_a)
    scan_id_b = UUID(args.scan_b)

    comparator = ScanComparator(db)
    result = await comparator.compare(scan_id_a, scan_id_b)

    await db.close()

    if args.output == "json":
        _print_compare_json(result, scan_id_a, scan_id_b)
    else:
        _print_compare_table(result)


def _print_compare_json(result, scan_id_a: UUID, scan_id_b: UUID) -> None:
    """Gibt den Vergleich als JSON aus."""
    data = {
        "scan_a": str(scan_id_a),
        "scan_b": str(scan_id_b),
        "new_findings": [
            {
                "title": f.title,
                "severity": f.severity.value,
                "cvss_score": f.cvss_score,
                "cve_id": f.cve_id,
                "host": f.target_host,
                "port": f.target_port,
            }
            for f in result.new_findings
        ],
        "fixed_findings": [
            {
                "title": f.title,
                "severity": f.severity.value,
                "cvss_score": f.cvss_score,
                "cve_id": f.cve_id,
                "host": f.target_host,
                "port": f.target_port,
            }
            for f in result.fixed_findings
        ],
        "unchanged_findings": len(result.unchanged_findings),
        "new_ports": result.new_ports,
        "closed_ports": result.closed_ports,
    }
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def _print_compare_table(result) -> None:
    """Gibt den Scan-Vergleich als formatierte Tabelle aus."""
    severity_icons: dict[str, str] = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🔵",
        "info": "⚪",
    }

    print()
    print("  SentinelClaw — Scan-Vergleich")
    print("  " + "=" * 60)
    print()
    print(result.summary)
    print()

    # Neue Findings detailliert anzeigen
    if result.new_findings:
        print("  --- Neue Findings (nur in Scan B) ---")
        for f in sorted(result.new_findings, key=lambda x: x.cvss_score, reverse=True):
            icon = severity_icons.get(f.severity.value, "⚪")
            port_str = f":{f.target_port}" if f.target_port else ""
            cve_str = f" ({f.cve_id})" if f.cve_id else ""
            print(f"  + {icon} {f.severity.value.upper():8s} {f.title}")
            print(f"                      {f.target_host}{port_str}{cve_str}")
        print()

    # Behobene Findings detailliert anzeigen
    if result.fixed_findings:
        print("  --- Behobene Findings (nur in Scan A) ---")
        for f in sorted(result.fixed_findings, key=lambda x: x.cvss_score, reverse=True):
            icon = severity_icons.get(f.severity.value, "⚪")
            port_str = f":{f.target_port}" if f.target_port else ""
            print(f"  - {icon} {f.severity.value.upper():8s} {f.title}")
            print(f"                      {f.target_host}{port_str}")
        print()

    # Port-Änderungen anzeigen
    if result.new_ports:
        print("  --- Neu geöffnete Ports ---")
        for p in result.new_ports:
            host = p.get("host_address", p.get("host", "?"))
            port = p.get("port", "?")
            svc = p.get("service", "")
            print(f"  + {host}:{port}/{p.get('protocol', 'tcp')}  {svc}")
        print()

    if result.closed_ports:
        print("  --- Geschlossene Ports ---")
        for p in result.closed_ports:
            host = p.get("host_address", p.get("host", "?"))
            port = p.get("port", "?")
            svc = p.get("service", "")
            print(f"  - {host}:{port}/{p.get('protocol', 'tcp')}  {svc}")
        print()


if __name__ == "__main__":
    main()
