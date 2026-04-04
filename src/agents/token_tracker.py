"""
Token-Budget-Tracking für SentinelClaw.

Zählt den Token-Verbrauch pro Scan, warnt bei 80%,
stoppt bei 100%. Verhindert unkontrollierte LLM-Kosten.
"""

from src.shared.logging_setup import get_logger

logger = get_logger(__name__)

WARN_THRESHOLD = 0.8  # Warnung bei 80%


class TokenTracker:
    """Verfolgt den Token-Verbrauch eines Scans gegen ein Budget."""

    def __init__(self, budget: int) -> None:
        self._budget = budget
        self._prompt_tokens = 0
        self._completion_tokens = 0
        self._warned = False

    def add_usage(self, prompt_tokens: int, completion_tokens: int) -> None:
        """Registriert Token-Verbrauch eines LLM-Aufrufs."""
        self._prompt_tokens += prompt_tokens
        self._completion_tokens += completion_tokens

        total = self.total_used
        percent = total / self._budget if self._budget > 0 else 0

        if percent >= WARN_THRESHOLD and not self._warned:
            self._warned = True
            logger.warning(
                "Token-Budget bei 80%",
                used=total,
                budget=self._budget,
                percent=round(percent * 100),
            )

        if self.is_budget_exceeded():
            logger.error(
                "Token-Budget erschöpft",
                used=total,
                budget=self._budget,
            )

    @property
    def total_used(self) -> int:
        """Gesamter Token-Verbrauch."""
        return self._prompt_tokens + self._completion_tokens

    @property
    def remaining(self) -> int:
        """Verbleibende Tokens."""
        return max(0, self._budget - self.total_used)

    @property
    def percent_used(self) -> float:
        """Prozentualer Verbrauch (0.0 bis 1.0+)."""
        if self._budget <= 0:
            return 0.0
        return self.total_used / self._budget

    def is_budget_exceeded(self) -> bool:
        """Prüft ob das Budget überschritten ist."""
        return self.total_used >= self._budget

    def should_warn(self) -> bool:
        """Prüft ob die Warnschwelle erreicht ist."""
        return self.percent_used >= WARN_THRESHOLD

    def summary(self) -> dict:
        """Gibt eine Zusammenfassung des Verbrauchs zurück."""
        return {
            "prompt_tokens": self._prompt_tokens,
            "completion_tokens": self._completion_tokens,
            "total_used": self.total_used,
            "budget": self._budget,
            "remaining": self.remaining,
            "percent_used": round(self.percent_used * 100, 1),
        }
