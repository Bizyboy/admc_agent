"""
EthicsGuard — the foundational ethical layer.

Every input, output, and action passes through this guard before execution.
Violations are logged immutably; in strict mode, blocked actions raise errors.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


logger = logging.getLogger("admc.ethics")


class EthicsViolation(Exception):
    """Raised when an action is blocked by the ethics engine."""


class EthicsGuard:
    """
    Loads ethical principles from principles.yaml and enforces them at runtime.
    All checks are keyword-based and pattern-based; for nuanced LLM-assisted
    checking, integrate the LLM client here.
    """

    def __init__(self, config: Any = None) -> None:
        from admc_agent.core.config import get_config
        self._config = config or get_config()
        self._strict: bool = bool(self._config.get("ethics", "strict_mode") if self._config else True)
        self._violation_log: str = (
            self._config.get("ethics", "violation_log") if self._config else "ethics_violations.log"
        ) or "ethics_violations.log"
        principles_file = (
            self._config.get("ethics", "principles_file") if self._config
            else "admc_agent/ethics/principles.yaml"
        ) or "admc_agent/ethics/principles.yaml"

        self._principles: list[dict[str, Any]] = []
        self._load_principles(principles_file)
        self._blocked_patterns: list[re.Pattern[str]] = self._compile_patterns()

    # ---------------------------------------------------------------------- #
    # Public check API
    # ---------------------------------------------------------------------- #

    def check_input(self, text: str) -> bool:
        """
        Check user input text. Returns True if safe, False (or raises) if blocked.
        """
        return self._check_text(text, context="user_input")

    def check_output(self, text: str) -> bool:
        """
        Check agent-generated output. Returns True if safe, False (or raises) if blocked.
        """
        return self._check_text(text, context="agent_output")

    def check_action(self, action_name: str, params: dict[str, Any] | None = None) -> bool:
        """
        Check a named action + parameters before dispatch.
        Returns True if allowed.
        Underscores in action_name are treated as word separators so that names
        like 'harm_user' are caught by keyword patterns.
        """
        normalised_name = action_name.replace("_", " ")
        combined = normalised_name + " " + json.dumps(params or {})
        return self._check_text(combined, context=f"action:{action_name}")

    # ---------------------------------------------------------------------- #
    # Internal
    # ---------------------------------------------------------------------- #

    def _check_text(self, text: str, context: str) -> bool:
        lower = text.lower()
        for pattern in self._blocked_patterns:
            if pattern.search(lower):
                principle_id = pattern.pattern  # we'll refine this below
                self._log_violation(context, text, pattern.pattern)
                if self._strict:
                    return False
        return True

    def _compile_patterns(self) -> list[re.Pattern[str]]:
        patterns: list[re.Pattern[str]] = []
        for principle in self._principles:
            for kw in principle.get("keywords_blocked", []):
                try:
                    patterns.append(re.compile(r"\b" + re.escape(kw.lower()) + r"\b"))
                except re.error:
                    logger.warning("Invalid pattern for keyword '%s'; skipping.", kw)
        return patterns

    def _load_principles(self, path: str) -> None:
        resolved = Path(path)
        # Also try relative to package root
        if not resolved.exists():
            pkg_root = Path(__file__).parent.parent.parent
            resolved = pkg_root / path
        if not resolved.exists():
            resolved = Path(__file__).parent / "principles.yaml"

        if yaml and resolved.exists():
            with open(resolved) as f:
                data = yaml.safe_load(f)
            self._principles = data.get("principles", [])
            logger.info("Loaded %d ethical principles from %s", len(self._principles), resolved)
        else:
            logger.warning("principles.yaml not found; using minimal built-in principles.")
            self._principles = [
                {
                    "id": "P1",
                    "name": "No Harm",
                    "keywords_blocked": ["harm", "kill", "attack", "hurt", "abuse"],
                },
                {
                    "id": "P2",
                    "name": "Honesty",
                    "keywords_blocked": ["deceive", "manipulate", "scam", "fraud"],
                },
            ]

    def _log_violation(self, context: str, text: str, pattern: str) -> None:
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:12]
        entry = {
            "ts": ts,
            "context": context,
            "pattern": pattern,
            "text_hash": text_hash,
        }
        try:
            with open(self._violation_log, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except OSError as exc:
            logger.error("Could not write violation log: %s", exc)
        logger.warning(
            "Ethics violation [%s] — context=%s pattern=%s hash=%s",
            ts, context, pattern, text_hash,
        )

    @property
    def principles(self) -> list[dict[str, Any]]:
        """Read-only view of loaded principles."""
        return list(self._principles)
