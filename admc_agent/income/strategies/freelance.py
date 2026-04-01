"""
Freelance Task Automation strategy.

Helps prepare and manage freelance service offerings (e.g., writing, coding,
data analysis) that can be listed on platforms like Fiverr or Upwork.
Zero startup cost — uses the agent's reasoning capability to draft proposals.
"""
from __future__ import annotations

import logging
from typing import Any

from admc_agent.income.strategies.base import IncomeStrategy

logger = logging.getLogger("admc.income.freelance")


class FreelanceStrategy(IncomeStrategy):
    """
    Automates the creation of freelance service proposals and listings.
    Generates professional gig descriptions and proposal templates using the LLM.
    """

    name = "freelance_automation"
    description = (
        "Draft freelance service listings and client proposals for platforms "
        "like Fiverr or Upwork using the agent's writing and reasoning capabilities."
    )

    _SERVICE_TEMPLATES = [
        "AI-powered blog writing and SEO content",
        "Python automation scripts for business workflows",
        "Data analysis and visualisation reports",
        "Technical documentation and README writing",
        "ChatGPT prompt engineering and fine-tuning consulting",
    ]

    def can_execute(self) -> bool:
        try:
            from admc_agent.reasoning.llm_client import LLMClient
            client = LLMClient(self._config)
            return client._client is not None
        except Exception:
            return False

    def execute(self, service: str | None = None) -> dict[str, Any]:
        service = service or self._SERVICE_TEMPLATES[0]
        try:
            from admc_agent.reasoning.llm_client import LLMClient
            client = LLMClient(self._config)
            gig_desc = client.complete([
                {
                    "role": "system",
                    "content": (
                        "You are an expert freelancer. Write a compelling Fiverr/Upwork gig listing "
                        "that attracts clients. Be specific, professional, and highlight unique value."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Write a gig listing for: {service}",
                },
            ])
            proposal = client.complete([
                {
                    "role": "system",
                    "content": "Write a short, personalised outreach proposal template for a freelancer.",
                },
                {
                    "role": "user",
                    "content": f"Outreach template for service: {service}",
                },
            ])
            logger.info("Freelance assets generated for: %s", service)
            return {
                "success": True,
                "message": f"Generated gig listing and proposal for '{service}'",
                "gig_description": gig_desc,
                "proposal_template": proposal,
                "estimated_revenue": self.estimated_yield(),
            }
        except Exception as exc:
            logger.error("Freelance strategy failed: %s", exc)
            return {"success": False, "message": str(exc), "estimated_revenue": 0.0}

    def estimated_yield(self) -> float:
        # A single freelance gig typically earns $15–$150
        return 30.0

    def get_service_ideas(self) -> list[str]:
        return list(self._SERVICE_TEMPLATES)
