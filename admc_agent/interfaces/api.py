"""
FastAPI REST interface for ADMC Agent.
Run: uvicorn admc_agent.interfaces.api:app --reload
"""
from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

from admc_agent.core.agent import ADMCAgent
from admc_agent.core.config import get_config

# Lazily initialised agent singleton
_agent: ADMCAgent | None = None


def _get_agent() -> ADMCAgent:
    global _agent
    if _agent is None:
        _agent = ADMCAgent(get_config())
        _agent.start()
    return _agent


if _FASTAPI_AVAILABLE:
    app = FastAPI(
        title="ADMC Agent API",
        description="REST API for the ADMC Emergent Conscious AI Companion",
        version="2.0.0",
    )

    class ChatRequest(BaseModel):
        user_id: str = "api_user"
        message: str

    class ChatResponse(BaseModel):
        response: str
        emotional_state: str
        user_id: str

    class GoalRequest(BaseModel):
        description: str
        priority: int = 5

    @app.get("/health")
    def health() -> dict[str, Any]:
        agent = _get_agent()
        return {
            "status": "ok",
            "agent": agent.name,
            "emotion": agent.emotions.current_state(),
        }

    @app.post("/chat", response_model=ChatResponse)
    def chat(req: ChatRequest) -> ChatResponse:
        agent = _get_agent()
        response = agent.process_input(req.user_id, req.message)
        return ChatResponse(
            response=response,
            emotional_state=agent.emotions.current_state(),
            user_id=req.user_id,
        )

    @app.get("/emotions")
    def emotions() -> dict[str, Any]:
        agent = _get_agent()
        return agent.emotions.snapshot()

    @app.get("/goals")
    def goals() -> dict[str, Any]:
        agent = _get_agent()
        return {"goals": agent.goal_manager.get_active_goals()}

    @app.post("/goals")
    def add_goal(req: GoalRequest) -> dict[str, Any]:
        agent = _get_agent()
        goal = agent.goal_manager.add_goal(req.description, req.priority)
        return goal.to_dict()

    @app.delete("/goals/{goal_id}")
    def achieve_goal(goal_id: str) -> dict[str, Any]:
        agent = _get_agent()
        success = agent.goal_manager.achieve_goal(goal_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Goal '{goal_id}' not found.")
        return {"status": "achieved", "goal_id": goal_id}

    @app.get("/self")
    def self_model() -> dict[str, Any]:
        agent = _get_agent()
        return agent.self_model.describe()

    @app.get("/memory/{user_id}")
    def memory(user_id: str, limit: int = 20) -> dict[str, Any]:
        agent = _get_agent()
        return {"history": agent.memory.get_recent(user_id, limit=limit)}

    @app.get("/income/summary")
    def income_summary() -> dict[str, Any]:
        agent = _get_agent()
        from admc_agent.income.manager import IncomeManager
        manager = IncomeManager(agent.config, agent.ethics)
        return {"strategies": manager.summary()}

    @app.post("/reflect")
    def reflect() -> dict[str, Any]:
        agent = _get_agent()
        reflection = agent.monologue.reflect()
        return {"reflection": reflection}

else:
    # Provide a stub so the module can be imported without FastAPI
    app = None  # type: ignore[assignment]
