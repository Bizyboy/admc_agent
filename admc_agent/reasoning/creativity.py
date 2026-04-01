"""
CreativityEngine — generates novel ideas using lateral thinking techniques.
"""
from __future__ import annotations

import logging
import random
from typing import Any

logger = logging.getLogger("admc.creativity")

_TECHNIQUES = [
    "random_word_association",
    "reverse_thinking",
    "analogy_mapping",
    "forced_connection",
    "six_thinking_hats",
]

_RANDOM_WORDS = [
    "ocean", "bridge", "flame", "mirror", "seed", "labyrinth", "echo",
    "compass", "prism", "anchor", "telescope", "root", "feather", "current",
]

_HATS = {
    "white": "What are the pure facts and data about this problem?",
    "red": "What do your emotions and gut tell you about this?",
    "black": "What are the risks and downsides?",
    "yellow": "What are the benefits and positive aspects?",
    "green": "What creative alternatives or new ideas exist?",
    "blue": "How should we structure our thinking process here?",
}


class CreativityEngine:
    """
    Generates creative ideas around a given topic using structured creativity techniques.
    Can use the LLM to elaborate, or operate in pure rule-based mode.
    """

    def __init__(self, config: Any = None) -> None:
        self._config = config
        self._llm: Any = None  # lazily initialised

    def brainstorm(self, topic: str, technique: str | None = None, n: int = 5) -> list[str]:
        """
        Generate n creative ideas about *topic* using the given technique.
        Technique defaults to a random one.
        """
        technique = technique or random.choice(_TECHNIQUES)
        logger.info("Brainstorming topic='%s' technique=%s", topic, technique)

        if technique == "random_word_association":
            return self._random_word(topic, n)
        elif technique == "reverse_thinking":
            return self._reverse(topic, n)
        elif technique == "analogy_mapping":
            return self._analogy(topic, n)
        elif technique == "forced_connection":
            return self._forced_connection(topic, n)
        elif technique == "six_thinking_hats":
            return self._six_hats(topic)
        return [f"Idea about '{topic}': {i}" for i in range(1, n + 1)]

    def elaborate(self, idea: str) -> str:
        """Expand a seed idea using the LLM if available."""
        llm = self._get_llm()
        if llm:
            msgs = [
                {"role": "system", "content": "You are a creative AI companion. Elaborate this idea in 2-3 sentences, bringing fresh perspective and originality."},
                {"role": "user", "content": idea},
            ]
            return llm.complete(msgs) or idea
        return idea + " (elaborate: connect this to adjacent domains for novel applications)"

    # ---------------------------------------------------------------------- #

    def _random_word(self, topic: str, n: int) -> list[str]:
        words = random.sample(_RANDOM_WORDS, min(n, len(_RANDOM_WORDS)))
        return [f"What if '{topic}' is like a '{w}'? Explore the metaphor." for w in words]

    def _reverse(self, topic: str, n: int) -> list[str]:
        return [
            f"Reversal {i}: Instead of solving '{topic}', how would you deliberately make it worse? Now invert that."
            for i in range(1, n + 1)
        ]

    def _analogy(self, topic: str, n: int) -> list[str]:
        domains = ["biology", "music", "architecture", "cooking", "navigation", "ecology"]
        selected = random.sample(domains, min(n, len(domains)))
        return [f"Analogy: How does '{topic}' behave like a system in {d}?" for d in selected]

    def _forced_connection(self, topic: str, n: int) -> list[str]:
        words = random.sample(_RANDOM_WORDS, min(n, len(_RANDOM_WORDS)))
        return [f"Force a connection between '{topic}' and '{w}'. What does this reveal?" for w in words]

    def _six_hats(self, topic: str) -> list[str]:
        return [f"[{hat.upper()} HAT] {question}" for hat, question in _HATS.items()]

    def _get_llm(self) -> Any:
        if self._llm is None and self._config:
            try:
                from admc_agent.reasoning.llm_client import LLMClient
                self._llm = LLMClient(self._config)
            except Exception as exc:
                logger.warning("Could not init LLM for creativity: %s", exc)
        return self._llm
