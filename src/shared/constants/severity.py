"""
Zentrale Severity-Konstanten für SentinelClaw.

Definiert einmalig alle Severity-bezogenen Mappings.
Wird überall importiert statt copy-paste.
"""

# CVSS-Schätzung nach Severity (wenn kein exakter Score verfügbar)
SEVERITY_CVSS_MAP: dict[str, float] = {
    "critical": 9.5,
    "high": 7.5,
    "medium": 5.0,
    "low": 2.5,
    "info": 0.0,
}

# Icons für CLI- und Markdown-Ausgabe
SEVERITY_ICONS: dict[str, str] = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
    "info": "⚪",
}

# Sortier-Reihenfolge (Critical zuerst)
SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}
