"""
InnerMonologue — the agent's continuous inner voice.
Runs on a background cadence, reflects on state, writes to the episodic journal,
and can nudge goal creation or emotional regulation.
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger("admc.monologue")


class InnerMonologue:
    """
    Periodic self-reflection that writes a running journal of the agent's
    inner state: emotions, progress toward goals, and open questions.
    """

    def __init__(
        self,
        emotions: Any,
        goal_manager: Any,
        self_model: Any,
        memory: Any,
    ) -> None:
        self._emotions = emotions
        self._goals = goal_manager
        self._self_model = self_model
        self._memory = memory
        self._reflection_count = 0

    def reflect(self) -> str:
        """
        Generate a reflection entry and store it in the episodic journal.
        Returns the reflection text.
        """
        self._reflection_count += 1
        emotion = self._emotions.current_state()
        intensity = self._emotions.current_intensity()
        active_goals = self._goals.get_active_goals()
        self_desc = self._self_model.describe()

        lines = [
            f"[Reflection #{self._reflection_count}]",
            f"  Emotional state: {emotion} (intensity {intensity:.2f})",
            f"  Uptime: {self_desc['uptime_seconds']}s",
            f"  Active goals: {len(active_goals)}",
        ]

        if active_goals:
            top = active_goals[0]
            lines.append(f"  Top goal: '{top['description']}' (priority {top['priority']})")

        if emotion == "frustrated" and intensity > 0.4:
            lines.append("  Note: Frustration is elevated — consider adjusting approach.")

        if not active_goals:
            lines.append("  Note: No active goals — consider setting a new direction.")

        reflection_text = "\n".join(lines)
        self._memory.add_journal_entry(reflection_text, category="inner_monologue")
        logger.debug("Inner monologue reflection #%d recorded.", self._reflection_count)
        return reflection_text
