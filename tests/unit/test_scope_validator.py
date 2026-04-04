"""Unit-Tests für den Scope-Validator."""

from datetime import datetime, timedelta, timezone

from src.shared.scope_validator import ScopeValidator
from src.shared.types.scope import PentestScope


def _make_scope(**kwargs) -> PentestScope:
    """Hilfsfunktion für Scope-Erstellung mit Defaults."""
    defaults = {"targets_include": ["10.10.10.0/24"]}
    defaults.update(kwargs)
    return PentestScope(**defaults)


validator = ScopeValidator()


def test_target_in_scope():
    """Ziel im Scope wird erlaubt."""
    r = validator.validate("10.10.10.5", None, "nmap", _make_scope())
    assert r.allowed


def test_target_not_in_scope():
    """Ziel außerhalb des Scopes wird blockiert."""
    r = validator.validate("192.168.1.1", None, "nmap", _make_scope())
    assert not r.allowed
    assert r.check_name == "target_in_scope"


def test_target_excluded():
    """Explizit ausgeschlossenes Ziel wird blockiert."""
    scope = _make_scope(targets_exclude=["10.10.10.1"])
    r = validator.validate("10.10.10.1", None, "nmap", scope)
    assert not r.allowed
    assert r.check_name == "target_not_excluded"


def test_forbidden_loopback():
    """Loopback-Adressen werden immer blockiert."""
    scope = _make_scope(targets_include=["127.0.0.0/8"])
    r = validator.validate("127.0.0.1", None, "nmap", scope)
    assert not r.allowed
    assert r.check_name == "target_not_forbidden"


def test_forbidden_multicast():
    """Multicast-Adressen werden blockiert."""
    scope = _make_scope(targets_include=["224.0.0.0/4"])
    r = validator.validate("224.0.0.1", None, "nmap", scope)
    assert not r.allowed


def test_escalation_level_allowed():
    """Tool innerhalb der erlaubten Stufe wird akzeptiert."""
    scope = _make_scope(max_escalation_level=2)
    r = validator.validate("10.10.10.5", None, "nuclei", scope)
    assert r.allowed  # nuclei = Stufe 2


def test_escalation_level_blocked():
    """Tool über der erlaubten Stufe wird blockiert."""
    scope = _make_scope(max_escalation_level=2)
    r = validator.validate("10.10.10.5", None, "metasploit", scope)
    assert not r.allowed
    assert r.check_name == "escalation_level"


def test_unknown_tool_blocked():
    """Unbekanntes Tool wird blockiert."""
    r = validator.validate("10.10.10.5", None, "evil_hack_tool", _make_scope())
    assert not r.allowed


def test_port_excluded():
    """Ausgeschlossener Port wird blockiert."""
    scope = _make_scope(ports_exclude=[22])
    r = validator.validate("10.10.10.5", 22, "nmap", scope)
    assert not r.allowed
    assert r.check_name == "port_in_scope"


def test_port_allowed():
    """Port im erlaubten Bereich wird akzeptiert."""
    scope = _make_scope(ports_include="1-1000")
    r = validator.validate("10.10.10.5", 80, "nmap", scope)
    assert r.allowed


def test_time_window_expired():
    """Abgelaufenes Zeitfenster blockiert."""
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    scope = _make_scope(time_window_end=past)
    r = validator.validate("10.10.10.5", None, "nmap", scope)
    assert not r.allowed
    assert r.check_name == "time_window"


def test_time_window_not_started():
    """Noch nicht begonnenes Zeitfenster blockiert."""
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    scope = _make_scope(time_window_start=future)
    r = validator.validate("10.10.10.5", None, "nmap", scope)
    assert not r.allowed


def test_tool_allowlist():
    """Explizite Tool-Allowlist wird respektiert."""
    scope = _make_scope(allowed_tools=["nmap"])
    r = validator.validate("10.10.10.5", None, "nuclei", scope)
    assert not r.allowed
    assert r.check_name == "tool_allowed"


def test_domain_target():
    """Domain-Ziele funktionieren."""
    scope = _make_scope(targets_include=["scanme.nmap.org"])
    r = validator.validate("scanme.nmap.org", None, "nmap", scope)
    assert r.allowed


def test_wildcard_domain():
    """Wildcard-Domains funktionieren."""
    scope = _make_scope(targets_include=["*.test.de"])
    r = validator.validate("webapp.test.de", None, "nmap", scope)
    assert r.allowed


def test_empty_scope_blocks():
    """Leerer Scope (keine Targets) blockiert alles."""
    scope = PentestScope()
    r = validator.validate("10.10.10.5", None, "nmap", scope)
    assert not r.allowed
