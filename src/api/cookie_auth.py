"""Cookie-basierte Authentifizierung für die SentinelClaw REST-API.

Stellt Hilfsfunktionen zum Setzen und Löschen von Auth-Cookies bereit.
Verwendet das Double-Submit Cookie Pattern für CSRF-Schutz:
  - sc_session: HttpOnly Cookie mit JWT (nicht per JS lesbar)
  - sc_csrf: Lesbares Cookie (Frontend sendet Wert als X-CSRF-Token Header)
"""

import os

from fastapi.responses import JSONResponse


def set_auth_cookies(response: JSONResponse, token: str, csrf_token: str) -> None:
    """Setzt die Auth-Cookies nach erfolgreichem Login.

    Cookie-Lebensdauer wird aus den Settings geladen (konfigurierbar über UI).
    SameSite=Lax statt Strict damit OAuth-Redirects funktionieren.
    """
    from src.shared.settings_service import get_setting_int_sync

    is_secure = os.environ.get("SENTINEL_DEBUG", "true").lower() != "true"
    max_age = get_setting_int_sync("cookie_max_age_seconds", 3600)

    response.set_cookie(
        key="sc_session",
        value=token,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        path="/",
        max_age=max_age,
    )
    response.set_cookie(
        key="sc_csrf",
        value=csrf_token,
        httponly=False,
        secure=is_secure,
        samesite="lax",
        path="/",
        max_age=max_age,
    )


def clear_auth_cookies(response: JSONResponse) -> None:
    """Löscht alle Auth-Cookies beim Logout."""
    response.delete_cookie(key="sc_session", path="/")
    response.delete_cookie(key="sc_csrf", path="/")
