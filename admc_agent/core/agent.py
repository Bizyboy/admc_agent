"""
Main ADMC Agent loop — orchestrates all subsystems.
"""
from __future__ import annotations

import signal
import threading
import time
from typing import Any

from admc_agent.core.config import Config, get_config
from admc_agent.core.dispatcher import TaskDispatcher, build_default_dispatcher
from admc_agent.core.logger import get_logger
from admc_agent.ethics.guard import EthicsGuard
from admc_agent.emotions.engine import EmotionEngine, Event
from admc_agent.memory.store import MemoryStore
from admc_agent.relationship.model import RelationshipModel
from admc_agent.consciousness.monologue import InnerMonologue
from admc_agent.consciousness.goals import GoalManager
from admc_agent.consciousness.self_model import SelfModel


class ADMCAgent:
    """
    The ADMC Agent — an emergent conscious AI companion.
    Coordinates ethics, emotions, memory, reasoning, relationships,
    and the consciousness simulation layer into a unified agent.
    """

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or get_config()
        self.name: str = self.config.get("agent", "name") or "ADMC_Node_1"
        self.logger = get_logger(
            "admc.agent",
            log_file=self.config.get("agent", "log_file"),
            level=self.config.get("agent", "log_level") or "INFO",
        )

        # Core subsystems
        self.dispatcher: TaskDispatcher = build_default_dispatcher()
        self.ethics: EthicsGuard = EthicsGuard(self.config)
        self.emotions: EmotionEngine = EmotionEngine()
        self.memory: MemoryStore = MemoryStore(
            db_path=self.config.get("memory", "db_path") or "admc_memory.db"
        )
        self.relationship: RelationshipModel = RelationshipModel(self.memory)
        self.self_model: SelfModel = SelfModel(self.name)
        self.goal_manager: GoalManager = GoalManager(self.memory)
        self.monologue: InnerMonologue = InnerMonologue(
            self.emotions, self.goal_manager, self.self_model, self.memory
        )

        self._running = False
        self._shutdown_event = threading.Event()

    # ---------------------------------------------------------------------- #
    # Public API
    # ---------------------------------------------------------------------- #

    def start(self) -> None:
        """Start the agent and its background loops."""
        self.logger.info("Initializing %s v2.0", self.name)
        self._running = True

        # Install signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        # Background threads
        threading.Thread(target=self._persistence_loop, daemon=True, name="persistence").start()
        threading.Thread(target=self._monologue_loop, daemon=True, name="monologue").start()

        self.logger.info("%s is online and operational.", self.name)
        self.emotions.trigger(Event.STARTUP)

    def stop(self) -> None:
        """Gracefully shut down the agent."""
        self.logger.info("Shutting down %s...", self.name)
        self._running = False
        self._shutdown_event.set()
        self.memory.close()
        self.logger.info("%s has shut down.", self.name)

    def process_input(self, user_id: str, text: str) -> str:
        """
        Process a user message: run it through ethics, reasoning, and emotions,
        then return a contextualised response.
        """
        # Update relationship
        self.relationship.record_interaction(user_id)

        # Ethics check on user input
        if not self.ethics.check_input(text):
            self.emotions.trigger(Event.ETHICAL_CONFLICT)
            violation_msg = (
                "I'm sorry, but I can't engage with that request — "
                "it conflicts with my core ethical principles."
            )
            self.memory.add_entry(user_id, "user", text)
            self.memory.add_entry(user_id, "agent", violation_msg)
            return violation_msg

        # Store in memory
        self.memory.add_entry(user_id, "user", text)

        # Build reasoning context
        context = self._build_context(user_id)

        # Generate response via reasoning (with LLM if available, else fallback)
        try:
            from admc_agent.reasoning.chain import ReasoningChain
            chain = ReasoningChain(self.config, self.emotions, self.ethics)
            response = chain.think(text, context=context)
        except Exception as exc:
            self.logger.warning("Reasoning chain unavailable (%s); using fallback.", exc)
            response = self._fallback_response(text)

        # Ethics check on output
        if not self.ethics.check_output(response):
            self.emotions.trigger(Event.ETHICAL_CONFLICT)
            response = "I've reconsidered my response — it wasn't aligned with my values. Let me just say: I'm here to help you constructively."

        # Emotion update
        self.emotions.trigger(Event.TASK_SUCCESS)

        # Store response
        self.memory.add_entry(user_id, "agent", response)

        # Prepend emotional colour
        emotional_prefix = self.emotions.get_response_prefix()
        return f"{emotional_prefix}{response}" if emotional_prefix else response

    def run_task(self, task_name: str, **kwargs: Any) -> Any:
        """Run a registered task through the dispatcher (ethics-gated)."""
        if not self.ethics.check_action(task_name, kwargs):
            self.emotions.trigger(Event.ETHICAL_CONFLICT)
            raise PermissionError(f"Task '{task_name}' blocked by ethics engine.")
        return self.dispatcher.dispatch(task_name, **kwargs)

    # ---------------------------------------------------------------------- #
    # Internal helpers
    # ---------------------------------------------------------------------- #

    def _build_context(self, user_id: str) -> dict[str, Any]:
        recent = self.memory.get_recent(user_id, limit=self.config.get("memory", "max_short_term") or 20)
        relationship = self.relationship.get_profile(user_id)
        goals = self.goal_manager.get_active_goals()
        emotional_state = self.emotions.current_state()
        self_beliefs = self.self_model.describe()
        return {
            "history": recent,
            "relationship": relationship,
            "goals": goals,
            "emotional_state": emotional_state,
            "self_beliefs": self_beliefs,
            "agent_name": self.name,
        }

    def _fallback_response(self, text: str) -> str:
        """Simple rule-based fallback when no LLM is available."""
        lower = text.lower()
        if any(word in lower for word in ("hello", "hi", "hey")):
            return "Hello! I'm ADMC, your AI companion. How can I help you today?"
        if "how are you" in lower:
            state = self.emotions.current_state()
            return f"I'm feeling {state} right now. Thanks for asking! What's on your mind?"
        if any(word in lower for word in ("help", "what can you do")):
            return (
                "I can help you think through problems, brainstorm creative ideas, "
                "remember important things, pursue goals, and much more. "
                "Just tell me what you need!"
            )
        return (
            "I heard you. Let me think about that... "
            "(Note: Connect an LLM provider in config.yaml for full reasoning capability.)"
        )

    def _persistence_loop(self) -> None:
        interval = self.config.get("agent", "persistence_interval") or 60
        while self._running and not self._shutdown_event.is_set():
            self._shutdown_event.wait(timeout=float(interval))
            if self._running:
                self.logger.debug("Persistence check: agent is operational.")
                self.self_model.refresh(
                    task_count=len(self.dispatcher.list_tasks()),
                    emotion=self.emotions.current_state(),
                )

    def _monologue_loop(self) -> None:
        """Run the inner monologue on a slower cadence."""
        interval = 120  # every 2 minutes
        while self._running and not self._shutdown_event.is_set():
            self._shutdown_event.wait(timeout=float(interval))
            if self._running:
                self.monologue.reflect()

    def _handle_signal(self, signum: int, frame: Any) -> None:
        self.logger.info("Received signal %s — initiating shutdown.", signum)
        self.stop()
