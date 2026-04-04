#!/usr/bin/env python3
"""Schneller Test-Scan für M3-Verifizierung."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.shared.logging_setup import setup_logging
setup_logging("WARNING")

from src.agents.nemoclaw_runtime import NemoClawRuntime
from src.agents.recon.agent import ReconAgent
from src.shared.types.scope import PentestScope

async def main():
    runtime = NemoClawRuntime()
    scope = PentestScope(targets_include=["scanme.nmap.org"], max_escalation_level=2)
    agent = ReconAgent(runtime=runtime, scope=scope)
    result = await agent.run_reconnaissance("scanme.nmap.org", ports="22,80,443")

    print(f"HOSTS: {result.total_hosts}")
    print(f"PORTS: {result.total_open_ports}")
    for p in result.open_ports:
        print(f"  {p.host}:{p.port}/{p.protocol} {p.service} {p.version}")
    print(f"VULNS: {result.total_vulnerabilities}")
    print(f"TURNS: {result.phases_completed}")
    print(f"TOKENS: {result.total_tokens_used}")
    print(f"DAUER: {result.scan_duration_seconds:.1f}s")
    if result.errors:
        print(f"ERRORS: {result.errors}")
    print("---SUMMARY---")
    print(result.agent_summary[:1500])

asyncio.run(main())
