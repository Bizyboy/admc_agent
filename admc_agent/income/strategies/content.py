"""
Content Generation strategy.

Generates SEO-optimised articles or README files for GitHub repos that can
be monetised via GitHub Sponsors, affiliate links, or sold as templates.
Requires: LLM provider configured.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from admc_agent.income.strategies.base import IncomeStrategy

logger = logging.getLogger("admc.income.content")


class ContentGenerationStrategy(IncomeStrategy):
    """
    Generates written content (blog posts, README files, documentation)
    that can be published and monetised.
    Zero startup cost — uses the agent's own LLM capability.
    """

    name = "content_generation"
    description = (
        "Generate SEO-optimised articles, GitHub README files, or documentation "
        "for monetisation via GitHub Sponsors, affiliate links, or content platforms."
    )

    def can_execute(self) -> bool:
        """Requires an LLM to be configured."""
        try:
            from admc_agent.reasoning.llm_client import LLMClient
            client = LLMClient(self._config)
            return client._client is not None
        except Exception:
            return False

    def execute(self, topic: str = "AI productivity tools", content_format: str = "blog") -> dict[str, Any]:
        try:
            from admc_agent.reasoning.llm_client import LLMClient
            client = LLMClient(self._config)
            prompt = self._build_prompt(topic, content_format)
            content = client.complete([
                {"role": "system", "content": "You are an expert content writer creating high-quality, SEO-optimised content."},
                {"role": "user", "content": prompt},
            ])
            filename = f"content_{int(time.time())}.md"
            with open(filename, "w") as f:
                f.write(content)
            logger.info("Content generated: %s (%d chars)", filename, len(content))
            return {
                "success": True,
                "message": f"Generated {content_format} article on '{topic}' → {filename}",
                "estimated_revenue": self.estimated_yield(),
                "filename": filename,
                "chars": len(content),
            }
        except Exception as exc:
            logger.error("Content generation failed: %s", exc)
            return {"success": False, "message": str(exc), "estimated_revenue": 0.0}

    def estimated_yield(self) -> float:
        # Conservative estimate: $1–$5 per article sold/used
        return 2.50

    def _build_prompt(self, topic: str, content_format: str) -> str:
        if content_format == "readme":
            return (
                f"Write a comprehensive, well-structured GitHub README for a project about '{topic}'. "
                "Include: project description, features, installation, usage examples, contributing guide, "
                "and license section. Use Markdown. Make it compelling and professional."
            )
        return (
            f"Write a 600-900 word SEO-optimised blog post about '{topic}'. "
            "Include: an engaging introduction, 3-4 sections with subheadings, actionable tips, "
            "and a conclusion with a call to action. Format in Markdown."
        )
