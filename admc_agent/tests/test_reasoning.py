"""
Tests for reasoning and creativity modules.
"""
import pytest
from unittest.mock import MagicMock, patch

from admc_agent.reasoning.creativity import CreativityEngine
from admc_agent.core.dispatcher import TaskDispatcher, build_default_dispatcher


class TestTaskDispatcher:
    def test_register_and_dispatch(self):
        d = TaskDispatcher()
        d.register("ping", lambda: "pong")
        result = d.dispatch("ping")
        assert result == "pong"

    def test_unknown_task_raises(self):
        d = TaskDispatcher()
        with pytest.raises(ValueError, match="Unknown task"):
            d.dispatch("nonexistent_task")

    def test_list_tasks(self):
        d = build_default_dispatcher()
        tasks = d.list_tasks()
        assert "heartbeat" in tasks
        assert "status" in tasks

    def test_heartbeat_task(self):
        d = build_default_dispatcher()
        result = d.dispatch("heartbeat")
        assert result == "heartbeat_ok"

    def test_status_task(self):
        d = build_default_dispatcher()
        result = d.dispatch("status")
        assert result["status"] == "running"
        assert "platform" in result
        assert "python" in result

    def test_no_exec_of_arbitrary_code(self):
        """Verify that arbitrary code strings cannot be executed."""
        d = build_default_dispatcher()
        with pytest.raises(ValueError):
            d.dispatch("print('injected')")

    def test_task_with_kwargs(self):
        d = TaskDispatcher()
        d.register("greet", lambda name: f"Hello {name}")
        result = d.dispatch("greet", name="World")
        assert result == "Hello World"


class TestCreativityEngine:
    def test_brainstorm_returns_list(self):
        engine = CreativityEngine()
        ideas = engine.brainstorm("climate change", technique="random_word_association", n=3)
        assert isinstance(ideas, list)
        assert len(ideas) == 3

    def test_brainstorm_reverse_thinking(self):
        engine = CreativityEngine()
        ideas = engine.brainstorm("productivity", technique="reverse_thinking", n=2)
        assert len(ideas) == 2
        assert all("Reversal" in idea for idea in ideas)

    def test_brainstorm_analogy_mapping(self):
        engine = CreativityEngine()
        ideas = engine.brainstorm("education", technique="analogy_mapping", n=3)
        assert len(ideas) == 3

    def test_brainstorm_six_hats(self):
        engine = CreativityEngine()
        ideas = engine.brainstorm("startup idea", technique="six_thinking_hats")
        assert len(ideas) == 6

    def test_brainstorm_forced_connection(self):
        engine = CreativityEngine()
        ideas = engine.brainstorm("healthcare", technique="forced_connection", n=4)
        assert len(ideas) == 4

    def test_brainstorm_random_technique(self):
        engine = CreativityEngine()
        ideas = engine.brainstorm("sustainability")
        assert len(ideas) > 0

    def test_elaborate_without_llm(self):
        engine = CreativityEngine()  # no config → no LLM
        result = engine.elaborate("Seed idea about renewable energy")
        assert "Seed idea" in result

    def test_all_ideas_are_strings(self):
        engine = CreativityEngine()
        for technique in ["random_word_association", "reverse_thinking",
                          "analogy_mapping", "forced_connection", "six_thinking_hats"]:
            ideas = engine.brainstorm("test topic", technique=technique, n=3)
            assert all(isinstance(idea, str) for idea in ideas)
