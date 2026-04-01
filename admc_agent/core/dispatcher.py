"""
Safe task dispatcher — replaces the exec()-based execute_task().
Maps task names to pre-registered Python callables; unknown tasks are rejected.
"""
from __future__ import annotations

import threading
from typing import Any, Callable

from admc_agent.core.logger import get_logger

logger = get_logger("admc.dispatcher")


class TaskDispatcher:
    """Registry of approved tasks. Tasks must be registered before they can run."""

    def __init__(self) -> None:
        self._registry: dict[str, Callable[..., Any]] = {}
        self._lock = threading.Lock()

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        """Register a callable under a task name."""
        with self._lock:
            self._registry[name] = fn
        logger.debug("Registered task: %s", name)

    def dispatch(self, task_name: str, **kwargs: Any) -> Any:
        """
        Dispatch a task by name with optional keyword arguments.
        Raises ValueError if the task is not registered.
        """
        with self._lock:
            fn = self._registry.get(task_name)
        if fn is None:
            logger.warning("Unknown task requested: '%s' — rejected.", task_name)
            raise ValueError(f"Unknown task: '{task_name}'")
        logger.info("Dispatching task: %s", task_name)
        try:
            result = fn(**kwargs)
            logger.info("Task '%s' completed successfully.", task_name)
            return result
        except Exception as exc:
            logger.error("Task '%s' raised an error: %s", task_name, exc)
            raise

    def list_tasks(self) -> list[str]:
        with self._lock:
            return list(self._registry.keys())


# --------------------------------------------------------------------------- #
# Built-in safe tasks
# --------------------------------------------------------------------------- #

def _task_heartbeat() -> str:
    logger.info("Heartbeat: agent is operational.")
    return "heartbeat_ok"


def _task_status() -> dict[str, Any]:
    import platform
    import time
    return {
        "status": "running",
        "platform": platform.system(),
        "python": platform.python_version(),
        "epoch": int(time.time()),
    }


def build_default_dispatcher() -> TaskDispatcher:
    """Return a dispatcher pre-loaded with the built-in safe tasks."""
    d = TaskDispatcher()
    d.register("heartbeat", _task_heartbeat)
    d.register("status", _task_status)
    return d
