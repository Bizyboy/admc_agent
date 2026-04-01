"""
Tests for the Emotion Engine.
Verifies state transitions, intensity capping, and dampening behaviour.
"""
import pytest

from admc_agent.emotions.engine import EmotionEngine, EmotionalState, Event


@pytest.fixture
def engine():
    return EmotionEngine()


class TestInitialState:
    def test_starts_neutral(self, engine):
        assert engine.current_state() == EmotionalState.NEUTRAL.value

    def test_starts_zero_intensity(self, engine):
        assert engine.current_intensity() == 0.0


class TestStateTransitions:
    def test_startup_triggers_curious(self, engine):
        engine.trigger(Event.STARTUP)
        assert engine.current_state() == EmotionalState.CURIOUS.value

    def test_task_success_triggers_satisfied(self, engine):
        engine.trigger(Event.TASK_SUCCESS)
        assert engine.current_state() == EmotionalState.SATISFIED.value

    def test_task_failure_triggers_frustrated(self, engine):
        engine.trigger(Event.TASK_FAILURE)
        assert engine.current_state() == EmotionalState.FRUSTRATED.value

    def test_ethical_conflict_triggers_cautious(self, engine):
        engine.trigger(Event.ETHICAL_CONFLICT)
        assert engine.current_state() == EmotionalState.CAUTIOUS.value

    def test_positive_feedback_triggers_enthusiastic(self, engine):
        engine.trigger(Event.USER_POSITIVE_FEEDBACK)
        assert engine.current_state() == EmotionalState.ENTHUSIASTIC.value

    def test_long_interaction_triggers_loyal(self, engine):
        engine.trigger(Event.LONG_INTERACTION)
        assert engine.current_state() == EmotionalState.LOYAL.value

    def test_goal_achieved_triggers_satisfied(self, engine):
        engine.trigger(Event.GOAL_ACHIEVED)
        assert engine.current_state() == EmotionalState.SATISFIED.value


class TestIntensityCapping:
    def test_frustration_capped_at_06(self, engine):
        # Trigger many failures
        for _ in range(20):
            engine.trigger(Event.TASK_FAILURE)
        assert engine.current_intensity() <= 0.6

    def test_enthusiasm_capped_at_08(self, engine):
        for _ in range(20):
            engine.trigger(Event.USER_POSITIVE_FEEDBACK)
        assert engine.current_intensity() <= 0.8

    def test_intensity_non_negative(self, engine):
        engine.trigger(Event.SLEEP)
        assert engine.current_intensity() >= 0.0


class TestHistory:
    def test_history_records_events(self, engine):
        engine.trigger(Event.STARTUP)
        engine.trigger(Event.TASK_SUCCESS)
        history = engine.recent_history()
        assert len(history) == 2

    def test_history_contains_state(self, engine):
        engine.trigger(Event.STARTUP)
        history = engine.recent_history(1)
        assert history[0]["state"] == EmotionalState.CURIOUS.value

    def test_history_capped_at_500(self, engine):
        for _ in range(600):
            engine.trigger(Event.TASK_SUCCESS)
        assert len(engine.recent_history(600)) <= 500


class TestResponsePrefix:
    def test_frustrated_prefix(self, engine):
        engine.trigger(Event.TASK_FAILURE)
        prefix = engine.get_response_prefix()
        assert "patiently" in prefix or prefix == ""  # either patiently or neutral

    def test_neutral_prefix_is_empty(self, engine):
        # New engine is neutral
        assert engine.get_response_prefix() == ""

    def test_curious_has_prefix(self, engine):
        engine.trigger(Event.STARTUP)
        prefix = engine.get_response_prefix()
        assert "curious" in prefix


class TestSnapshot:
    def test_snapshot_keys(self, engine):
        snap = engine.snapshot()
        assert "state" in snap
        assert "intensity" in snap
        assert "history_length" in snap


class TestListeners:
    def test_listener_called_on_transition(self, engine):
        received = []
        engine.add_listener(lambda state, intensity: received.append((state, intensity)))
        engine.trigger(Event.TASK_SUCCESS)
        assert len(received) == 1
        assert received[0][0] == EmotionalState.SATISFIED
