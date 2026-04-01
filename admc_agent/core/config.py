"""
Configuration system for ADMC Agent.
Reads from config.yaml and environment variables, with sane defaults.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

_DEFAULTS: dict[str, Any] = {
    "agent": {
        "name": "ADMC_Node_1",
        "admin_uid": "admin",
        "persistence_interval": 60,
        "task_check_interval": 5,
        "log_file": "admc_agent.log",
        "log_level": "INFO",
    },
    "llm": {
        "provider": "openai",          # "openai" | "anthropic" | "ollama"
        "model": "gpt-4o-mini",
        "api_key_env": "OPENAI_API_KEY",
        "base_url": None,
        "timeout": 60,
        "max_tokens": 2048,
    },
    "memory": {
        "db_path": "admc_memory.db",
        "max_short_term": 20,
        "embedding_model": "text-embedding-3-small",
    },
    "ethics": {
        "principles_file": "admc_agent/ethics/principles.yaml",
        "violation_log": "ethics_violations.log",
        "strict_mode": True,
    },
    "income": {
        "enabled": False,
        "strategies": ["content_generation"],
    },
    "api": {
        "host": "0.0.0.0",
        "port": 8000,
    },
}


class Config:
    """Hierarchical configuration: env vars > config.yaml > defaults."""

    def __init__(self, config_path: str | None = None) -> None:
        self._data: dict[str, Any] = _deep_copy(_DEFAULTS)
        path = config_path or os.environ.get("ADMC_CONFIG", "config.yaml")
        if yaml and Path(path).exists():
            with open(path) as f:
                file_cfg = yaml.safe_load(f) or {}
            self._data = _deep_merge(self._data, file_cfg)
        self._apply_env_overrides()

    def get(self, *keys: str, default: Any = None) -> Any:
        """Retrieve a nested key using dot-path keys, e.g. get('llm', 'model')."""
        node: Any = self._data
        for k in keys:
            if not isinstance(node, dict):
                return default
            node = node.get(k)
            if node is None:
                return default
        return node

    def _apply_env_overrides(self) -> None:
        """Allow ENV vars like ADMC_LLM_MODEL to override config."""
        prefix = "ADMC_"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                parts = key[len(prefix):].lower().split("_", 1)
                if len(parts) == 2:
                    section, subkey = parts
                    if section in self._data and isinstance(self._data[section], dict):
                        self._data[section][subkey] = value


def _deep_copy(d: dict) -> dict:
    import copy
    return copy.deepcopy(d)


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# Module-level singleton
_config: Config | None = None


def get_config(config_path: str | None = None) -> Config:
    global _config
    if _config is None:
        _config = Config(config_path)
    return _config
