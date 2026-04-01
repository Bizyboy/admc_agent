"""
GoalManager — sets, prioritises, and tracks long-term goals.
Goals are persisted in the MemoryStore facts table.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

logger = logging.getLogger("admc.goals")

_GOALS_KEY = "agent:goals"


class Goal:
    def __init__(
        self,
        description: str,
        priority: int = 5,
        goal_id: str | None = None,
        created: float | None = None,
        status: str = "active",
    ) -> None:
        self.id = goal_id or str(uuid.uuid4())[:8]
        self.description = description
        self.priority = priority  # 1 (lowest) .. 10 (highest)
        self.created = created or time.time()
        self.status = status  # "active" | "achieved" | "abandoned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority,
            "created": self.created,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Goal":
        return cls(
            description=d["description"],
            priority=d.get("priority", 5),
            goal_id=d.get("id"),
            created=d.get("created"),
            status=d.get("status", "active"),
        )


class GoalManager:
    def __init__(self, memory: Any) -> None:
        self._memory = memory

    def add_goal(self, description: str, priority: int = 5) -> Goal:
        goal = Goal(description=description, priority=priority)
        goals = self._load()
        goals.append(goal)
        self._save(goals)
        logger.info("Goal added: [%s] %s (priority=%d)", goal.id, description, priority)
        return goal

    def achieve_goal(self, goal_id: str) -> bool:
        goals = self._load()
        for g in goals:
            if g.id == goal_id:
                g.status = "achieved"
                self._save(goals)
                logger.info("Goal achieved: [%s] %s", g.id, g.description)
                return True
        return False

    def abandon_goal(self, goal_id: str) -> bool:
        goals = self._load()
        for g in goals:
            if g.id == goal_id:
                g.status = "abandoned"
                self._save(goals)
                return True
        return False

    def get_active_goals(self) -> list[dict[str, Any]]:
        return sorted(
            [g.to_dict() for g in self._load() if g.status == "active"],
            key=lambda g: g["priority"],
            reverse=True,
        )

    def get_all_goals(self) -> list[dict[str, Any]]:
        return [g.to_dict() for g in self._load()]

    # ---------------------------------------------------------------------- #

    def _load(self) -> list[Goal]:
        data = self._memory.get_fact(_GOALS_KEY) or []
        return [Goal.from_dict(d) for d in data]

    def _save(self, goals: list[Goal]) -> None:
        self._memory.set_fact(_GOALS_KEY, [g.to_dict() for g in goals])
