"""Token-Blacklist für JWT-Revokation.

Verwaltet widerrufene JWT-Tokens über ihre jti (JWT ID).
Kombination aus In-Memory-Set (schnell) und DB-Persistenz (überlebt Neustarts).
"""

from datetime import UTC, datetime

from src.shared.logging_setup import get_logger

logger = get_logger(__name__)


class TokenBlacklist:
    """Verwaltet widerrufene JWT-Tokens für serverseitiges Logout."""

    def __init__(self) -> None:
        self._revoked: set[str] = set()

    async def load_from_db(self, db) -> int:
        """Lädt noch gültige revozierte Tokens aus der Datenbank.

        Wird beim Server-Start aufgerufen um den In-Memory-Cache
        mit persistierten Revokationen zu befüllen.
        """
        conn = await db.get_connection()
        now = datetime.now(UTC).isoformat()
        cursor = await conn.execute(
            "SELECT jti FROM revoked_tokens WHERE expires_at > ?",
            (now,),
        )
        rows = await cursor.fetchall()
        for row in rows:
            self._revoked.add(row[0])

        loaded = len(rows)
        if loaded:
            logger.info(f"{loaded} revozierte Tokens aus DB geladen")
        return loaded

    async def revoke(self, jti: str, expires_at: str, db) -> None:
        """Widerruft einen Token anhand seiner jti.

        Speichert sowohl in-memory als auch in der Datenbank
        für Persistenz über Server-Neustarts.
        """
        self._revoked.add(jti)
        now = datetime.now(UTC).isoformat()

        conn = await db.get_connection()
        await conn.execute(
            "INSERT OR IGNORE INTO revoked_tokens (jti, expires_at, revoked_at) "
            "VALUES (?, ?, ?)",
            (jti, expires_at, now),
        )
        await conn.commit()
        logger.info("Token revoziert", jti=jti)

    def is_revoked(self, jti: str) -> bool:
        """Prüft ob ein Token widerrufen wurde (O(1) Lookup)."""
        return jti in self._revoked

    async def cleanup_expired(self, db) -> int:
        """Entfernt abgelaufene Einträge aus DB und Memory.

        Tokens die bereits abgelaufen sind können sicher entfernt werden,
        da sie ohnehin nicht mehr gültig wären.
        """
        now = datetime.now(UTC).isoformat()
        conn = await db.get_connection()

        # Abgelaufene jti-Werte sammeln
        cursor = await conn.execute(
            "SELECT jti FROM revoked_tokens WHERE expires_at <= ?",
            (now,),
        )
        expired_rows = await cursor.fetchall()
        expired_jtis = {row[0] for row in expired_rows}

        if not expired_jtis:
            return 0

        # Aus DB und Memory entfernen
        await conn.execute(
            "DELETE FROM revoked_tokens WHERE expires_at <= ?",
            (now,),
        )
        await conn.commit()
        self._revoked -= expired_jtis

        logger.info(f"{len(expired_jtis)} abgelaufene Token-Revokationen bereinigt")
        return len(expired_jtis)


# Singleton-Instanz — wird beim Server-Start mit DB initialisiert
token_blacklist = TokenBlacklist()
