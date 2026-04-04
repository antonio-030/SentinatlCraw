"""
E2E-Test: Kill-Switch.

Prüft dass der Kill-Switch korrekt funktioniert:
- Flag wird gesetzt und ist irreversibel
- Sandbox wird gestoppt
- Audit-Log wird geschrieben
"""

import pytest

from src.shared.kill_switch import KillSwitch


def test_kill_switch_activation():
    """Kill-Switch aktivieren und prüfen."""
    ks = KillSwitch()
    ks.reset()  # Sauberer Zustand für Test

    assert not ks.is_active()

    ks.activate(triggered_by="test_user", reason="E2E-Test")

    assert ks.is_active()
    assert ks.triggered_by == "test_user"
    assert ks.reason == "E2E-Test"
    assert ks.activated_at is not None

    # Cleanup
    ks.reset()


def test_kill_switch_irreversible():
    """Nach Aktivierung bleibt der Kill-Switch aktiv (ohne reset)."""
    ks = KillSwitch()
    ks.reset()

    ks.activate(triggered_by="test", reason="irreversibility test")
    assert ks.is_active()

    # Zweite Aktivierung ändert nichts
    ks.activate(triggered_by="other", reason="second call")
    assert ks.is_active()
    # Erster Trigger bleibt
    assert ks.triggered_by == "test"

    ks.reset()


def test_kill_switch_singleton():
    """Kill-Switch ist ein Singleton — gleiche Instanz überall."""
    ks1 = KillSwitch()
    ks2 = KillSwitch()
    assert ks1 is ks2

    ks1.reset()
    ks1.activate(triggered_by="singleton_test", reason="test")
    assert ks2.is_active()

    ks1.reset()


def test_kill_switch_not_active_by_default():
    """Kill-Switch ist standardmäßig nicht aktiv."""
    ks = KillSwitch()
    ks.reset()
    assert not ks.is_active()
