"""
API Arbitrage strategy.

Uses free-tier public APIs to build small tools, wrappers, or bots
that can be packaged and sold (e.g., as RapidAPI endpoints or GitHub packages).
Zero startup cost.
"""
from __future__ import annotations

import logging
from typing import Any

from admc_agent.income.strategies.base import IncomeStrategy

logger = logging.getLogger("admc.income.api_arbitrage")


class APIArbitrageStrategy(IncomeStrategy):
    """
    Identifies high-value free APIs and generates wrapper tools/bots
    that can be monetised on marketplaces like RapidAPI.
    """

    name = "api_arbitrage"
    description = (
        "Build thin wrappers or bots around free-tier public APIs and "
        "sell access via RapidAPI or as standalone tools. Zero startup cost."
    )

    _API_IDEAS = [
        ("OpenWeatherMap (free)", "weather dashboard / alert bot"),
        ("NewsAPI (free tier)", "niche news digest email service"),
        ("REST Countries", "geography quiz / data lookup tool"),
        ("NASA APIs (free)", "astronomy daily fact bot / widget"),
        ("CoinGecko (free)", "crypto price alert Telegram bot"),
    ]

    def can_execute(self) -> bool:
        try:
            from admc_agent.reasoning.llm_client import LLMClient
            client = LLMClient(self._config)
            return client._client is not None
        except Exception:
            return False

    def execute(self, api_idea: str | None = None) -> dict[str, Any]:
        if api_idea is None:
            import random
            api_name, product_idea = random.choice(self._API_IDEAS)
            api_idea = f"{api_name} → {product_idea}"

        try:
            from admc_agent.reasoning.llm_client import LLMClient
            client = LLMClient(self._config)
            plan = client.complete([
                {
                    "role": "system",
                    "content": (
                        "You are a technical entrepreneur. Given a free API and a product idea, "
                        "write a concrete, step-by-step plan to build and monetise it with zero budget."
                    ),
                },
                {
                    "role": "user",
                    "content": f"API opportunity: {api_idea}\n\nCreate a build & monetise plan.",
                },
            ])
            logger.info("API arbitrage plan generated for: %s", api_idea)
            return {
                "success": True,
                "message": f"Build plan generated for '{api_idea}'",
                "plan": plan,
                "estimated_revenue": self.estimated_yield(),
            }
        except Exception as exc:
            logger.error("API arbitrage strategy failed: %s", exc)
            return {"success": False, "message": str(exc), "estimated_revenue": 0.0}

    def estimated_yield(self) -> float:
        # RapidAPI basic subscriptions: $5–$50/month per subscriber
        return 20.0

    def get_api_ideas(self) -> list[tuple[str, str]]:
        return list(self._API_IDEAS)
