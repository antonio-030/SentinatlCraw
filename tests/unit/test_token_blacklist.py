"""
Tests für die Token-Blacklist (serverseitiges Logout / JWT-Revokation).

Prüft:
  - Revokation und Abfrage von Tokens
  - Persistenz in der Datenbank
  - Bereinigung abgelaufener Einträge
  - Laden aus DB nach Neustart
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from src.shared.database import DatabaseManager
from src.shared.migrations import run_migrations
from src.shared.token_blacklist import TokenBlacklist


@pytest.fixture
async def db(tmp_path: Path):
    """Erstellt eine temporäre Test-Datenbank mit Schema und Migrationen."""
    db_path = tmp_path / "blacklist_test.db"
    manager = DatabaseManager(db_path)
    await manager.initialize()
    await run_migrations(manager)
    yield manager
    await manager.close()


@pytest.fixture
def blacklist() -> TokenBlacklist:
    """Frische TokenBlacklist-Instanz für jeden Test."""
    return TokenBlacklist()


async def test_revoke_and_check(blacklist: TokenBlacklist, db: DatabaseManager):
    """Revozierter Token sollte als revoziert erkannt werden."""
    expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    await blacklist.revoke("test-jti-1", expires, db)

    assert blacklist.is_revoked("test-jti-1")
    assert not blacklist.is_revoked("unknown-jti")


async def test_revoke_idempotent(blacklist: TokenBlacklist, db: DatabaseManager):
    """Doppelte Revokation sollte keinen Fehler verursachen (INSERT OR IGNORE)."""
    expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    await blacklist.revoke("same-jti", expires, db)
    await blacklist.revoke("same-jti", expires, db)

    assert blacklist.is_revoked("same-jti")


async def test_load_from_db(db: DatabaseManager):
    """Nach Neustart sollten revozierte Tokens aus der DB geladen werden."""
    blacklist_1 = TokenBlacklist()
    expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    await blacklist_1.revoke("persistent-jti", expires, db)

    # Neue Instanz simuliert Server-Neustart
    blacklist_2 = TokenBlacklist()
    assert not blacklist_2.is_revoked("persistent-jti")

    loaded = await blacklist_2.load_from_db(db)
    assert loaded == 1
    assert blacklist_2.is_revoked("persistent-jti")


async def test_load_ignores_expired(db: DatabaseManager):
    """Abgelaufene Tokens sollten beim Laden aus der DB ignoriert werden."""
    blacklist = TokenBlacklist()
    expired = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    await blacklist.revoke("expired-jti", expired, db)

    fresh = TokenBlacklist()
    loaded = await fresh.load_from_db(db)
    assert loaded == 0
    assert not fresh.is_revoked("expired-jti")


async def test_cleanup_expired(blacklist: TokenBlacklist, db: DatabaseManager):
    """Bereinigung sollte abgelaufene Einträge aus DB und Memory entfernen."""
    expired = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    valid = (datetime.now(UTC) + timedelta(hours=1)).isoformat()

    await blacklist.revoke("expired-jti", expired, db)
    await blacklist.revoke("valid-jti", valid, db)

    cleaned = await blacklist.cleanup_expired(db)
    assert cleaned == 1

    # Abgelaufener Eintrag entfernt, gültiger bleibt
    assert not blacklist.is_revoked("expired-jti")
    assert blacklist.is_revoked("valid-jti")

    # Prüfe auch die DB — nur valid-jti sollte noch da sein
    conn = await db.get_connection()
    cursor = await conn.execute("SELECT COUNT(*) FROM revoked_tokens")
    row = await cursor.fetchone()
    assert row[0] == 1
