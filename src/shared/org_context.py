"""Organisations-Kontext für Multi-Tenancy.

Stellt den aktuellen Organisations-Kontext bereit, der aus dem
JWT-Token extrahiert wird. Repositories nutzen diesen Kontext
um Daten auf die Organisation des Benutzers zu beschränken.
"""


class OrgContext:
    """Trägt die organization_id durch den Request-Lifecycle.

    system_admin mit org_id=None sieht alle Organisationen.
    """

    def __init__(self, org_id: str | None = None) -> None:
        self._org_id = org_id

    @property
    def org_id(self) -> str | None:
        """Aktuelle Organisations-ID oder None für Cross-Org-Zugriff."""
        return self._org_id

    @property
    def is_cross_org(self) -> bool:
        """True wenn der Benutzer organisationsübergreifend zugreifen darf."""
        return self._org_id is None

    def sql_filter(self, column: str = "organization_id") -> tuple[str, list[str]]:
        """Gibt SQL-WHERE-Fragment und Parameter für Org-Filterung zurück.

        Bei Cross-Org: Leeres Fragment (keine Einschränkung).
        Bei Org-Kontext: "AND organization_id = ?" mit Parameter.
        """
        if self.is_cross_org:
            return "", []
        return f"AND {column} = ?", [self._org_id]
