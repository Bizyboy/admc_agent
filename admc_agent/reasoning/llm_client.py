"""
LLM Client — thin wrapper supporting OpenAI, Anthropic, and Ollama backends.
Falls back gracefully if the selected provider is unavailable.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("admc.llm")


class LLMClient:
    """
    Unified LLM client.

    Supports:
      provider="openai"     — requires openai package + OPENAI_API_KEY
      provider="anthropic"  — requires anthropic package + ANTHROPIC_API_KEY
      provider="ollama"     — requires a running Ollama server
    """

    def __init__(self, config: Any = None) -> None:
        from admc_agent.core.config import get_config
        self._cfg = config or get_config()
        self._provider: str = (self._cfg.get("llm", "provider") or "openai").lower()
        self._model: str = self._cfg.get("llm", "model") or "gpt-4o-mini"
        self._timeout: int = int(self._cfg.get("llm", "timeout") or 60)
        self._max_tokens: int = int(self._cfg.get("llm", "max_tokens") or 2048)
        self._base_url: str | None = self._cfg.get("llm", "base_url")
        self._client: Any = None
        self._init_client()

    def _init_client(self) -> None:
        try:
            if self._provider == "openai":
                import os
                import openai  # type: ignore[import]
                key_env = self._cfg.get("llm", "api_key_env") or "OPENAI_API_KEY"
                api_key = os.environ.get(key_env)
                kwargs: dict[str, Any] = {}
                if api_key:
                    kwargs["api_key"] = api_key
                else:
                    logger.warning(
                        "LLM: env var '%s' is not set — OpenAI client may fail. "
                        "Set it in your environment or config.yaml.", key_env
                    )
                if self._base_url:
                    kwargs["base_url"] = self._base_url
                self._client = openai.OpenAI(**kwargs)
                logger.info("LLM: OpenAI client initialised (model=%s).", self._model)

            elif self._provider == "anthropic":
                import os
                import anthropic  # type: ignore[import]
                key_env = self._cfg.get("llm", "api_key_env") or "ANTHROPIC_API_KEY"
                api_key = os.environ.get(key_env)
                self._client = anthropic.Anthropic(api_key=api_key)
                logger.info("LLM: Anthropic client initialised (model=%s).", self._model)

            elif self._provider == "ollama":
                import requests  # type: ignore[import]
                self._client = requests  # use requests for Ollama HTTP API
                logger.info("LLM: Ollama client initialised (model=%s).", self._model)

            else:
                logger.warning("Unknown LLM provider '%s'; no client initialised.", self._provider)
        except ImportError as exc:
            logger.warning("LLM provider '%s' package not available: %s", self._provider, exc)
        except Exception as exc:
            logger.error("Failed to initialise LLM client: %s", exc)

    def complete(self, messages: list[dict[str, str]]) -> str:
        """
        Send a chat completion request and return the assistant message text.
        Returns an empty string if the client is unavailable.
        """
        if self._client is None:
            logger.warning("LLM client not available; returning empty response.")
            return ""
        try:
            if self._provider == "openai":
                return self._complete_openai(messages)
            elif self._provider == "anthropic":
                return self._complete_anthropic(messages)
            elif self._provider == "ollama":
                return self._complete_ollama(messages)
        except Exception as exc:
            logger.error("LLM completion error: %s", exc)
        return ""

    def _complete_openai(self, messages: list[dict[str, str]]) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            max_tokens=self._max_tokens,
            timeout=self._timeout,
        )
        return resp.choices[0].message.content or ""

    def _complete_anthropic(self, messages: list[dict[str, str]]) -> str:
        # Anthropic separates system message from user/assistant turns
        system_msgs = [m["content"] for m in messages if m["role"] == "system"]
        turn_msgs = [m for m in messages if m["role"] != "system"]
        system_text = "\n".join(system_msgs)
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system_text,
            messages=turn_msgs,
        )
        return resp.content[0].text if resp.content else ""

    def _complete_ollama(self, messages: list[dict[str, str]]) -> str:
        base = self._base_url or "http://localhost:11434"
        import json
        resp = self._client.post(
            f"{base}/api/chat",
            json={"model": self._model, "messages": messages, "stream": False},
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json().get("message", {}).get("content", "")
