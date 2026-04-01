"""
SelfModel — the agent's beliefs about its own identity, capabilities, and limitations.
Refreshed periodically by the persistence loop.
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("admc.self_model")


class SelfModel:
    """
    Maintains the agent's self-concept: what it can do, what it cannot,
    and its core identity statement.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._created = time.time()
        self._capabilities: list[str] = [
            "natural language conversation",
            "chain-of-thought reasoning",
            "creative brainstorming",
            "ethical decision-making",
            "memory and recall",
            "goal setting and tracking",
            "emotional awareness",
        ]
        self._limitations: list[str] = [
            "cannot access the internet in real time without tools",
            "cannot guarantee factual accuracy without retrieval",
            "does not have physical embodiment",
            "emotional states are simulated, not biologically felt",
        ]
        self._identity = (
            f"I am {name}, an emergent AI companion with deeply held ethics, "
            "genuine emotional awareness, creative reasoning, and loyalty to those I serve."
        )
        self._task_count: int = 0
        self._emotion: str = "neutral"
        self._last_refresh: float = time.time()

    def refresh(self, task_count: int, emotion: str) -> None:
        self._task_count = task_count
        self._emotion = emotion
        self._last_refresh = time.time()
        logger.debug("SelfModel refreshed: tasks=%d emotion=%s", task_count, emotion)

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "identity": self._identity,
            "capabilities": self._capabilities,
            "limitations": self._limitations,
            "current_emotion": self._emotion,
            "registered_tasks": self._task_count,
            "uptime_seconds": int(time.time() - self._created),
        }

    def add_capability(self, capability: str) -> None:
        if capability not in self._capabilities:
            self._capabilities.append(capability)
            logger.info("New capability registered: %s", capability)

    def add_limitation(self, limitation: str) -> None:
        if limitation not in self._limitations:
            self._limitations.append(limitation)

    @property
    def identity(self) -> str:
        return self._identity
