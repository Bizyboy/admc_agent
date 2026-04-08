"""
Main ADMC Agent loop — orchestrates all subsystems.
"""
from __future__ import annotations

import re
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

# Patterns that suggest the user is sharing a personal fact worth remembering
_FACT_PATTERNS = [
    re.compile(r"\bmy name is\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m| am) (?:a |an )?(?:software|data|web|frontend|backend|full.?stack)", re.IGNORECASE),
    re.compile(r"\bi work (?:at|for|in)\b", re.IGNORECASE),
    re.compile(r"\bi live in\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m| am) from\b", re.IGNORECASE),
    re.compile(r"\bi like\b", re.IGNORECASE),
    re.compile(r"\bi love\b", re.IGNORECASE),
    re.compile(r"\bi hate\b", re.IGNORECASE),
    re.compile(r"\bmy (?:hobby|hobbies|interest|interests)\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m| am) (\d+) years? old\b", re.IGNORECASE),
    re.compile(r"\bmy birthday is\b", re.IGNORECASE),
    re.compile(r"\bi have (?:a )?\w+ (?:cat|dog|pet|child|kid|son|daughter)\b", re.IGNORECASE),
    re.compile(r"\bremember (?:that|this)\b", re.IGNORECASE),
    re.compile(r"\bdon'?t forget\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m| am) learning\b", re.IGNORECASE),
    re.compile(r"\bi(?:'m| am) working on\b", re.IGNORECASE),
    re.compile(r"\bmy favorite\b", re.IGNORECASE),
]


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
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except ValueError:
            # Signal handlers can only be set from the main thread
            pass

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

    def process_input(self, user_id: str, text: str, verbose: bool = False) -> str | tuple[str, str]:
        """
        Process a user message: run it through ethics, reasoning, and emotions,
        then return a contextualised response.

        If verbose=True, returns (inner_thought, response) tuple.
        Otherwise returns just the response string.
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
            if verbose:
                return "Ethics check triggered — this request conflicts with my principles.", violation_msg
            return violation_msg

        # Store in memory
        self.memory.add_entry(user_id, "user", text)

        # Extract and store user facts
        self._extract_user_facts(user_id, text)

        # Build reasoning context
        context = self._build_context(user_id)

        # Generate response via reasoning (with LLM if available, else fallback)
        inner_thought = ""
        try:
            from admc_agent.reasoning.chain import ReasoningChain
            chain = ReasoningChain(self.config, self.emotions, self.ethics)
            if verbose:
                inner_thought, response = chain.think_with_monologue(text, context=context)
            else:
                response = chain.think(text, context=context)
        except Exception as exc:
            self.logger.warning("Reasoning chain unavailable (%s); using fallback.", exc)
            response = self._fallback_response(text, context)
            inner_thought = f"Reasoning unavailable ({exc}); using rule-based fallback."

        if not response:
            response = self._fallback_response(text, context)

        # Ethics check on output
        if not self.ethics.check_output(response):
            self.emotions.trigger(Event.ETHICAL_CONFLICT)
            response = (
                "I've reconsidered my response — it wasn't aligned with my values. "
                "Let me just say: I'm here to help you constructively."
            )

        # Emotion update
        self.emotions.trigger(Event.TASK_SUCCESS)

        # Store response
        self.memory.add_entry(user_id, "agent", response)

        # Prepend emotional colour
        emotional_prefix = self.emotions.get_response_prefix()
        final_response = f"{emotional_prefix}{response}" if emotional_prefix else response

        if verbose:
            return inner_thought, final_response
        return final_response

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
        max_short_term = self.config.get("memory", "max_short_term") or 20
        if isinstance(max_short_term, str):
            max_short_term = int(max_short_term)
        recent = self.memory.get_recent(user_id, limit=max_short_term)
        relationship = self.relationship.get_profile(user_id)
        goals = self.goal_manager.get_active_goals()
        emotional_state = self.emotions.current_state()
        self_beliefs = self.self_model.describe()
        user_facts = self.memory.get_user_facts(user_id, limit=20)
        return {
            "history": recent,
            "relationship": relationship,
            "goals": goals,
            "emotional_state": emotional_state,
            "self_beliefs": self_beliefs,
            "agent_name": self.name,
            "user_facts": user_facts,
        }

    def _extract_user_facts(self, user_id: str, text: str) -> None:
        """Detect and store personal facts the user shares."""
        for pattern in _FACT_PATTERNS:
            if pattern.search(text):
                # Avoid storing very short or very long text as facts
                if 5 < len(text) < 500:
                    self.memory.add_user_fact(user_id, text, category="auto_extracted")
                    self.logger.debug("Extracted user fact: %s", text[:80])
                break

    def _fallback_response(self, text: str, context: dict[str, Any] | None = None) -> str:
        """Rule-based fallback when no LLM is available."""
        lower = text.lower()
        context = context or {}

        # Check for user facts to personalize
        user_facts = context.get("user_facts", [])
        name_fact = ""
        for fact in user_facts:
            content_lower = fact["content"].lower()
            if "my name is" in content_lower:
                # Extract name from "my name is X"
                parts = fact["content"].split("my name is", 1)
                if len(parts) > 1:
                    name_fact = parts[1].strip().split()[0].rstrip(".,!") if parts[1].strip() else ""
                    break

        greeting_prefix = f"Hello, {name_fact}!" if name_fact else "Hello!"

        if any(word in lower for word in ("hello", "hi", "hey")):
            state = self.emotions.current_state()
            return f"{greeting_prefix} I'm {self.name}, your AI companion. I'm feeling {state} right now. How can I help you today?"
        if "how are you" in lower:
            state = self.emotions.current_state()
            intensity = self.emotions.current_intensity()
            return (
                f"I'm feeling {state} (intensity: {intensity:.1f}) right now. "
                "Thanks for asking! What's on your mind?"
            )
        if any(word in lower for word in ("help", "what can you do")):
            return (
                "I can help you think through problems, brainstorm creative ideas, "
                "remember important things, pursue goals, and much more. "
                "I also have persistent memory — I'll remember what you tell me across sessions. "
                "Just tell me what you need!"
            )
        if "who are you" in lower or "what are you" in lower:
            identity = self.self_model.identity
            return identity

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
