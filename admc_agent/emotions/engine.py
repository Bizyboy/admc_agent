"""
EmotionEngine — models the agent's internal emotional state.

Emotional states:
  neutral, curious, satisfied, frustrated, enthusiastic, cautious, loyal, warm

State transitions are triggered by discrete Events.  Dampening prevents runaway
accumulation of any single emotion.
"""
from __future__ import annotations

import logging
import threading
import time
from enum import Enum
from typing import Callable

logger = logging.getLogger("admc.emotions")


class EmotionalState(str, Enum):
    NEUTRAL = "neutral"
    CURIOUS = "curious"
    SATISFIED = "satisfied"
    FRUSTRATED = "frustrated"
    ENTHUSIASTIC = "enthusiastic"
    CAUTIOUS = "cautious"
    LOYAL = "loyal"
    WARM = "warm"


class Event(str, Enum):
    STARTUP = "startup"
    TASK_SUCCESS = "task_success"
    TASK_FAILURE = "task_failure"
    ETHICAL_CONFLICT = "ethical_conflict"
    NEW_TOPIC = "new_topic"
    REPEATED_FAILURE = "repeated_failure"
    LONG_INTERACTION = "long_interaction"
    USER_POSITIVE_FEEDBACK = "user_positive_feedback"
    USER_NEGATIVE_FEEDBACK = "user_negative_feedback"
    SLEEP = "sleep"
    WAKE = "wake"
    CREATIVE_TASK = "creative_task"
    GOAL_ACHIEVED = "goal_achieved"


# ---------------------------------------------------------------------------
# Transition table: event -> (new_state, intensity_delta)
# Intensity is a [0.0 .. 1.0] float for the current state.
# ---------------------------------------------------------------------------
_TRANSITIONS: dict[Event, tuple[EmotionalState, float]] = {
    Event.STARTUP: (EmotionalState.CURIOUS, 0.5),
    Event.TASK_SUCCESS: (EmotionalState.SATISFIED, 0.3),
    Event.TASK_FAILURE: (EmotionalState.FRUSTRATED, 0.2),
    Event.ETHICAL_CONFLICT: (EmotionalState.CAUTIOUS, 0.5),
    Event.NEW_TOPIC: (EmotionalState.CURIOUS, 0.4),
    Event.REPEATED_FAILURE: (EmotionalState.FRUSTRATED, 0.4),
    Event.LONG_INTERACTION: (EmotionalState.LOYAL, 0.3),
    Event.USER_POSITIVE_FEEDBACK: (EmotionalState.ENTHUSIASTIC, 0.4),
    Event.USER_NEGATIVE_FEEDBACK: (EmotionalState.CAUTIOUS, 0.3),
    Event.SLEEP: (EmotionalState.NEUTRAL, -0.2),
    Event.WAKE: (EmotionalState.CURIOUS, 0.2),
    Event.CREATIVE_TASK: (EmotionalState.ENTHUSIASTIC, 0.3),
    Event.GOAL_ACHIEVED: (EmotionalState.SATISFIED, 0.5),
}

# Damping caps per state
_INTENSITY_CAPS: dict[EmotionalState, float] = {
    EmotionalState.FRUSTRATED: 0.6,   # frustration is capped
    EmotionalState.ENTHUSIASTIC: 0.8,  # enthusiasm is moderated
    EmotionalState.CAUTIOUS: 0.7,
    EmotionalState.SATISFIED: 0.9,
    EmotionalState.CURIOUS: 0.9,
    EmotionalState.LOYAL: 1.0,        # loyalty can be total
    EmotionalState.WARM: 1.0,
    EmotionalState.NEUTRAL: 1.0,
}

# Response prefixes per state (for coloring agent replies)
_RESPONSE_PREFIXES: dict[EmotionalState, str] = {
    EmotionalState.NEUTRAL: "",
    EmotionalState.CURIOUS: "*(curious)* ",
    EmotionalState.SATISFIED: "*(satisfied)* ",
    EmotionalState.FRUSTRATED: "*(patiently)* ",
    EmotionalState.ENTHUSIASTIC: "*(enthusiastically)* ",
    EmotionalState.CAUTIOUS: "*(carefully)* ",
    EmotionalState.LOYAL: "*(warmly)* ",
    EmotionalState.WARM: "*(warmly)* ",
}


class EmotionEngine:
    """Thread-safe emotional state machine."""

    def __init__(self) -> None:
        self._state: EmotionalState = EmotionalState.NEUTRAL
        self._intensity: float = 0.0
        self._history: list[dict] = []
        self._lock = threading.Lock()
        self._listeners: list[Callable[[EmotionalState, float], None]] = []

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def trigger(self, event: Event) -> None:
        """Process an event and update emotional state."""
        transition = _TRANSITIONS.get(event)
        if transition is None:
            return
        new_state, delta = transition

        with self._lock:
            if new_state != self._state:
                # Transition — reset intensity for the new state
                self._state = new_state
                self._intensity = max(0.0, min(delta, _INTENSITY_CAPS[new_state]))
            else:
                # Same state — accumulate intensity with cap
                cap = _INTENSITY_CAPS[new_state]
                self._intensity = min(self._intensity + delta, cap)

            # Natural decay toward neutral over time
            self._intensity = max(self._intensity, 0.0)

            snapshot = {
                "ts": time.time(),
                "event": event.value,
                "state": self._state.value,
                "intensity": round(self._intensity, 3),
            }
            self._history.append(snapshot)
            if len(self._history) > 500:
                self._history = self._history[-500:]

        logger.debug(
            "Emotion: event=%s → state=%s intensity=%.2f",
            event.value, self._state.value, self._intensity,
        )

        for listener in self._listeners:
            try:
                listener(self._state, self._intensity)
            except Exception as exc:
                logger.warning("Emotion listener error: %s", exc)

    def current_state(self) -> str:
        with self._lock:
            return self._state.value

    def current_intensity(self) -> float:
        with self._lock:
            return self._intensity

    def get_response_prefix(self) -> str:
        """Return a text prefix that reflects the current emotional state."""
        with self._lock:
            state = self._state
        return _RESPONSE_PREFIXES.get(state, "")

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "state": self._state.value,
                "intensity": self._intensity,
                "history_length": len(self._history),
            }

    def add_listener(self, fn: Callable[[EmotionalState, float], None]) -> None:
        self._listeners.append(fn)

    def recent_history(self, n: int = 10) -> list[dict]:
        with self._lock:
            return list(self._history[-n:])
