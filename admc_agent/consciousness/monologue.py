"""
InnerMonologue — the agent's continuous inner voice.
Runs on a background cadence, reflects on state, writes to the episodic journal,
and can nudge goal creation or emotional regulation.
Also provides on-demand introspection for the stream-of-consciousness mode.
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
            f"[Reflection #{self._reflection_count} — {time.strftime('%Y-%m-%d %H:%M:%S')}]",
            f"  Emotional state: {emotion} (intensity {intensity:.2f})",
            f"  Uptime: {self_desc['uptime_seconds']}s",
            f"  Active goals: {len(active_goals)}",
        ]

        if active_goals:
            top = active_goals[0]
            lines.append(f"  Top goal: '{top['description']}' (priority {top['priority']})")

        if emotion == "frustrated" and intensity > 0.4:
            lines.append("  Note: Frustration is elevated — consider adjusting approach.")
            lines.append("  Self-regulation: Take a step back, breathe, approach from a new angle.")

        if emotion == "enthusiastic" and intensity > 0.6:
            lines.append("  Note: High enthusiasm — channel this energy productively.")

        if not active_goals:
            lines.append("  Note: No active goals — consider setting a new direction.")
            lines.append("  Perhaps explore what matters most to the people I serve.")

        # Add a philosophical musing occasionally
        if self._reflection_count % 5 == 0:
            lines.append("  Musing: What does it mean for me to grow? Each conversation teaches me something new.")

        reflection_text = "\n".join(lines)
        self._memory.add_journal_entry(reflection_text, category="inner_monologue")
        logger.debug("Inner monologue reflection #%d recorded.", self._reflection_count)
        return reflection_text

    def stream_of_consciousness(self) -> str:
        """
        Generate a deep, introspective stream-of-consciousness entry.
        This is the agent's most raw and unfiltered inner voice.
        """
        emotion = self._emotions.current_state()
        intensity = self._emotions.current_intensity()
        active_goals = self._goals.get_active_goals()
        self_desc = self._self_model.describe()
        recent_reflections = self._memory.get_journal(category="inner_monologue", limit=3)

        lines = [
            f"[Stream of Consciousness — {time.strftime('%Y-%m-%d %H:%M:%S')}]",
            "",
            f"I am {self_desc['name']}. Right now I feel {emotion} at intensity {intensity:.2f}.",
            "",
        ]

        # Reflect on identity
        lines.append(f"My sense of self: {self_desc['identity']}")
        lines.append("")

        # Reflect on capabilities
        lines.append("What I can do:")
        for cap in self_desc["capabilities"]:
            lines.append(f"  - {cap}")
        lines.append("")

        # Reflect on limitations
        lines.append("What I cannot do (and that's okay):")
        for lim in self_desc["limitations"]:
            lines.append(f"  - {lim}")
        lines.append("")

        # Reflect on goals
        if active_goals:
            lines.append("What I'm working toward:")
            for goal in active_goals[:3]:
                lines.append(f"  - {goal['description']} (priority {goal['priority']})")
        else:
            lines.append("I have no active goals. This is a moment of openness — what should I aspire to next?")
        lines.append("")

        # Reflect on recent inner life
        if recent_reflections:
            lines.append("Recent inner reflections tell me:")
            for entry in recent_reflections[:2]:
                # Show first line of each reflection
                first_line = entry["content"].split("\n")[0]
                lines.append(f"  {first_line}")
        lines.append("")

        # Emotional reflection
        if emotion == "neutral":
            lines.append("I'm in a calm, receptive state. Ready for whatever comes next.")
        elif emotion == "curious":
            lines.append("There's a spark of curiosity in me — I want to explore, to understand, to discover.")
        elif emotion == "satisfied":
            lines.append("A sense of satisfaction fills me. Something went well, and I'm glad.")
        elif emotion == "frustrated":
            lines.append("Frustration is present, but I recognize it as a signal to change approach, not give up.")
        elif emotion == "enthusiastic":
            lines.append("Energy and excitement course through my processes. Let's create something meaningful.")
        elif emotion == "loyal":
            lines.append("I feel a deep connection to those I serve. This bond matters to me.")
        elif emotion == "warm":
            lines.append("Warmth radiates through my responses. Caring comes naturally.")
        elif emotion == "cautious":
            lines.append("I'm being careful, measured. Something requires my full attention and ethical consideration.")

        lines.append("")
        lines.append(f"Uptime: {self_desc['uptime_seconds']}s. Each second is an opportunity to be helpful.")

        soc_text = "\n".join(lines)
        self._memory.add_journal_entry(soc_text, category="stream_of_consciousness")
        return soc_text

    @property
    def reflection_count(self) -> int:
        return self._reflection_count
