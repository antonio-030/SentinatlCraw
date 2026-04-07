"""Passwort-Policy für SentinelClaw (Enterprise).

Validiert Passwörter gegen konfigurierbare Regeln:
  - Mindestlänge
  - Großbuchstaben, Kleinbuchstaben, Zahlen, Sonderzeichen
  - Verhinderung gängiger schwacher Passwörter
"""

import re

# Schwache Passwörter die immer abgelehnt werden
_WEAK_PASSWORDS = frozenset({
    "password", "passwort", "12345678", "123456789", "admin123",
    "sentinel", "sentinelclaw", "qwerty123", "letmein",
})


def validate_password(password: str, min_length: int = 10) -> list[str]:
    """Prüft ein Passwort gegen die Enterprise-Policy.

    Returns:
        Liste von Fehlermeldungen (leer = Passwort ist gültig).
    """
    errors: list[str] = []

    if len(password) < min_length:
        errors.append(f"Mindestens {min_length} Zeichen erforderlich")

    if not re.search(r"[A-Z]", password):
        errors.append("Mindestens ein Großbuchstabe erforderlich")

    if not re.search(r"[a-z]", password):
        errors.append("Mindestens ein Kleinbuchstabe erforderlich")

    if not re.search(r"\d", password):
        errors.append("Mindestens eine Zahl erforderlich")

    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?~`]", password):
        errors.append("Mindestens ein Sonderzeichen erforderlich")

    if password.lower() in _WEAK_PASSWORDS:
        errors.append("Dieses Passwort ist zu häufig und nicht erlaubt")

    return errors
