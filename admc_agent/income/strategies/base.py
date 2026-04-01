"""
Base class for income strategies.

All strategies expose the same interface:
  can_execute() -> bool       — True if preconditions are met
  execute()     -> dict       — run the strategy, return result metadata
  estimated_yield() -> float  — estimated revenue per execution in USD
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IncomeStrategy(ABC):
    """Abstract base for all income strategies."""

    name: str = "base"
    description: str = "Base income strategy."

    def __init__(self, config: Any = None) -> None:
        self._config = config

    @abstractmethod
    def can_execute(self) -> bool:
        """Return True if all preconditions for this strategy are currently met."""

    @abstractmethod
    def execute(self) -> dict[str, Any]:
        """
        Execute the strategy.
        Returns a dict with at minimum:
          {"success": bool, "message": str, "estimated_revenue": float}
        """

    @abstractmethod
    def estimated_yield(self) -> float:
        """Return an estimated USD yield per execution of this strategy."""

    def summary(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "can_execute": self.can_execute(),
            "estimated_yield_usd": self.estimated_yield(),
        }
