"""
MCP-Tool: parse_output — Strukturierte Analyse von Scan-Rohdaten.

Parst nmap-XML und nuclei-JSONL in strukturiertes Python/JSON.
Rein lokale Verarbeitung, keine Sandbox nötig.
"""

import json
import xml.etree.ElementTree as ET
from typing import Any

from src.shared.constants.severity import SEVERITY_ORDER
from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


def parse_output(raw_output: str, output_format: str = "nmap_xml") -> dict[str, Any]:
    """Parst Scan-Rohdaten in strukturiertes Format.

    Unterstützte Formate:
    - nmap_xml: nmap -oX Ausgabe
    - nuclei_jsonl: nuclei -jsonl Ausgabe
    - plaintext: Unstrukturierter Text → Zusammenfassung
    """
    if not raw_output or not raw_output.strip():
        return {"format": output_format, "data": [], "summary": "Keine Daten"}

    parsers = {
        "nmap_xml": _parse_nmap_xml_to_dict,
        "nuclei_jsonl": _parse_nuclei_jsonl_to_dict,
        "plaintext": _parse_plaintext,
    }

    parser = parsers.get(output_format)
    if parser is None:
        raise ValueError(
            f"Unbekanntes Format: '{output_format}'. "
            f"Erlaubt: {', '.join(parsers.keys())}"
        )

    try:
        result = parser(raw_output)
        logger.debug(
            "Output geparsed",
            format=output_format,
            entries=len(result.get("data", [])),
        )
        return result
    except Exception as error:
        logger.warning(
            "Parse-Fehler, Fallback auf Plaintext",
            format=output_format,
            error=str(error),
        )
        return _parse_plaintext(raw_output)


def _parse_nmap_xml_to_dict(xml_output: str) -> dict[str, Any]:
    """Parst nmap XML in ein strukturiertes Dict."""
    try:
        root = ET.fromstring(xml_output)
    except ET.ParseError as error:
        raise ValueError(f"Ungültiges nmap XML: {error}")

    hosts: list[dict] = []
    for host_elem in root.findall(".//host"):
        status = host_elem.find("status")
        if status is None or status.get("state") != "up":
            continue

        addr = host_elem.find("address")
        address = addr.get("addr", "unknown") if addr is not None else "unknown"

        hostname_elem = host_elem.find("hostnames/hostname")
        hostname = hostname_elem.get("name", "") if hostname_elem is not None else ""

        ports: list[dict] = []
        for port_elem in host_elem.findall(".//port"):
            state_elem = port_elem.find("state")
            service_elem = port_elem.find("service")

            ports.append({
                "port": int(port_elem.get("portid", 0)),
                "protocol": port_elem.get("protocol", "tcp"),
                "state": state_elem.get("state", "unknown") if state_elem is not None else "unknown",
                "service": service_elem.get("name", "") if service_elem is not None else "",
                "version": (
                    f"{service_elem.get('product', '')} {service_elem.get('version', '')}".strip()
                    if service_elem is not None else ""
                ),
            })

        hosts.append({
            "address": address,
            "hostname": hostname,
            "ports": ports,
        })

    # Zusammenfassung erstellen
    total_open = sum(len([p for p in h["ports"] if p["state"] == "open"]) for h in hosts)

    return {
        "format": "nmap_xml",
        "data": hosts,
        "summary": f"{len(hosts)} Hosts aktiv, {total_open} offene Ports",
    }


def _parse_nuclei_jsonl_to_dict(jsonl_output: str) -> dict[str, Any]:
    """Parst nuclei JSONL in ein strukturiertes Dict."""
    findings: list[dict] = []
    severity_counts: dict[str, int] = {}

    for line in jsonl_output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        info = data.get("info", {})
        severity = info.get("severity", "info").lower()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

        classification = info.get("classification", {})
        cve_ids = classification.get("cve-id", [])

        findings.append({
            "template_id": data.get("template-id", data.get("templateID", "")),
            "name": info.get("name", ""),
            "severity": severity,
            "description": info.get("description", ""),
            "host": data.get("host", ""),
            "matched_at": data.get("matched-at", data.get("matchedAt", "")),
            "cve_id": cve_ids[0] if cve_ids else None,
        })

    # Nach Schweregrad sortieren (Critical zuerst)
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f["severity"], 5))

    return {
        "format": "nuclei_jsonl",
        "data": findings,
        "severity_counts": severity_counts,
        "summary": (
            f"{len(findings)} Findings: "
            + ", ".join(f"{count}x {sev}" for sev, count in sorted(severity_counts.items()))
        ),
    }


def _parse_plaintext(text: str) -> dict[str, Any]:
    """Fallback-Parser für unstrukturierten Text."""
    lines = text.strip().split("\n")
    return {
        "format": "plaintext",
        "data": lines,
        "summary": f"{len(lines)} Zeilen Ausgabe",
    }
