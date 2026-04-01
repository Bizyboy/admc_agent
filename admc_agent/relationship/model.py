"""
RelationshipModel — tracks familiarity, trust, and communication style per user.

Loyalty and warmth grow through consistent positive interactions ("bond formation curve").
"""
from __future__ import annotations

import logging
import math
import time
from typing import Any

logger = logging.getLogger("admc.relationship")

# Familiarity grows on a logarithmic curve: score = log(1 + interactions)
# Trust is stored as an explicit float [0.0 .. 1.0]


class RelationshipModel:
    """
    Manages per-user relationship state backed by the MemoryStore facts table.
    """

    def __init__(self, memory: Any) -> None:
        self._memory = memory

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def record_interaction(self, user_id: str) -> None:
        """Call this every time a user sends a message."""
        profile = self._load(user_id)
        profile["interactions"] += 1
        profile["last_seen"] = time.time()
        # Familiarity grows logarithmically: slow at first, then levels off.
        # log1p(n) = log(1+n) — avoids log(0) and produces a smooth [0, ∞) curve.
        # Rounded to 3 d.p. for storage efficiency.
        profile["familiarity"] = round(math.log1p(profile["interactions"]), 3)
        self._save(user_id, profile)
        logger.debug(
            "Relationship[%s]: interactions=%d familiarity=%.3f",
            user_id, profile["interactions"], profile["familiarity"],
        )

    def record_positive_feedback(self, user_id: str) -> None:
        profile = self._load(user_id)
        profile["trust"] = min(1.0, profile["trust"] + 0.05)
        profile["positive_count"] += 1
        self._save(user_id, profile)

    def record_negative_feedback(self, user_id: str) -> None:
        profile = self._load(user_id)
        profile["trust"] = max(0.0, profile["trust"] - 0.03)
        profile["negative_count"] += 1
        self._save(user_id, profile)

    def set_preference(self, user_id: str, key: str, value: Any) -> None:
        """Store a communication preference for a user (e.g., verbose=False)."""
        profile = self._load(user_id)
        profile["preferences"][key] = value
        self._save(user_id, profile)

    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        profile = self._load(user_id)
        return profile["preferences"].get(key, default)

    def get_profile(self, user_id: str) -> dict[str, Any]:
        return self._load(user_id)

    def loyalty_level(self, user_id: str) -> str:
        """Return a human-readable loyalty tier."""
        profile = self._load(user_id)
        familiarity = profile["familiarity"]
        trust = profile["trust"]
        score = familiarity * 0.6 + trust * 10 * 0.4
        if score >= 5.0:
            return "deep_loyalty"
        elif score >= 3.0:
            return "trusted_friend"
        elif score >= 1.5:
            return "acquaintance"
        return "new_contact"

    # ---------------------------------------------------------------------- #
    # Internal
    # ---------------------------------------------------------------------- #

    def _load(self, user_id: str) -> dict[str, Any]:
        key = f"relationship:{user_id}"
        data = self._memory.get_fact(key)
        if data is None:
            data = {
                "user_id": user_id,
                "interactions": 0,
                "familiarity": 0.0,
                "trust": 0.5,
                "positive_count": 0,
                "negative_count": 0,
                "last_seen": None,
                "preferences": {},
            }
        return data

    def _save(self, user_id: str, profile: dict[str, Any]) -> None:
        self._memory.set_fact(f"relationship:{user_id}", profile)
