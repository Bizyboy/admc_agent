"""
IncomeManager — orchestrates all income strategies.
"""
from __future__ import annotations

import logging
from typing import Any

from admc_agent.income.strategies.base import IncomeStrategy
from admc_agent.income.strategies.content import ContentGenerationStrategy
from admc_agent.income.strategies.freelance import FreelanceStrategy
from admc_agent.income.strategies.api_arbitrage import APIArbitrageStrategy

logger = logging.getLogger("admc.income")

_REGISTRY: dict[str, type[IncomeStrategy]] = {
    "content_generation": ContentGenerationStrategy,
    "freelance_automation": FreelanceStrategy,
    "api_arbitrage": APIArbitrageStrategy,
}


class IncomeManager:
    """
    Manages and executes income-generating strategies.
    Strategies must pass an ethics check before execution.
    """

    def __init__(self, config: Any = None, ethics_guard: Any = None) -> None:
        self._config = config
        self._ethics = ethics_guard
        self._strategies: dict[str, IncomeStrategy] = {}
        self._enabled: bool = False
        if config:
            self._enabled = bool(config.get("income", "enabled"))
            enabled_strategies: list[str] = config.get("income", "strategies") or []
            for name in enabled_strategies:
                self.register_strategy(name)

    def register_strategy(self, name: str) -> None:
        cls = _REGISTRY.get(name)
        if cls is None:
            logger.warning("Unknown income strategy '%s'; skipping.", name)
            return
        self._strategies[name] = cls(self._config)
        logger.info("Income strategy registered: %s", name)

    def run_strategy(self, name: str, **kwargs: Any) -> dict[str, Any]:
        if not self._enabled:
            return {"success": False, "message": "Income module is disabled. Enable in config.yaml."}

        strategy = self._strategies.get(name)
        if strategy is None:
            return {"success": False, "message": f"Strategy '{name}' not registered."}

        if not strategy.can_execute():
            return {"success": False, "message": f"Preconditions not met for '{name}'."}

        # Ethics gate: ensure the strategy action is ethical
        if self._ethics and not self._ethics.check_action(f"income:{name}", kwargs):
            return {"success": False, "message": "Blocked by ethics engine."}

        return strategy.execute(**kwargs)

    def run_all_executable(self) -> list[dict[str, Any]]:
        results = []
        for name, strategy in self._strategies.items():
            if strategy.can_execute():
                results.append({"strategy": name, **self.run_strategy(name)})
        return results

    def summary(self) -> list[dict[str, Any]]:
        return [s.summary() for s in self._strategies.values()]

    @staticmethod
    def available_strategies() -> list[str]:
        return list(_REGISTRY.keys())
