"""
ADMC MIND - The Master Orchestrator
=====================================
This is the single object that IS ADMC running.

Every message flows through all four layers:
  Core (soul) -> Consciousness (think) -> Ethics (evaluate) -> Communication (express)

The API is called LAST, only to generate natural language.
All reasoning, ethics, and values happen BEFORE the API is called.
"""

import os
import requests
import threading
from datetime import datetime

from .soul import (
    load_soul, save_soul, wake_up, sleep,
    add_to_short_term, get_waking_thought,
    update_emotion, record_growth
)
from admc.core import CoreLayer
from admc.ethics import EthicsLayer
from admc.consciousness import ConsciousnessEngine
from admc.learning import LearningEngine
from admc.communication import CommunicationEngine


class ADMCMind:

    def __init__(self, api_key, api_url="https://api.x.ai/v1/chat/completions", model="grok-3-mini"):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

        # Load the soul - this IS ADMC
        self.soul = load_soul()
        wake_up(self.soul)
        save_soul(self.soul)

        # Initialize all four layers
        self.core = CoreLayer()
        self.ethics = EthicsLayer(self.core, api_key, api_url, model)
        self.consciousness = ConsciousnessEngine(api_key, api_url, model)
        self.learning = LearningEngine(api_key, api_url, model)
        self.communication = CommunicationEngine(api_key, api_url, model)

        # Start background consciousness (thinks every 10 min when idle)
        self.consciousness.start_background(self.soul)

    def wake_message(self):
        """What ADMC says or thinks when coming online."""
        return get_waking_thought(self.soul)

    def process(self, user_input, user_id="default"):
        """
        Full pipeline for every message:
        1. Generate inner monologue (what does this person need?)
        2. Build ethical, identity-aware prompt
        3. Call API for language generation
        4. Ethics evaluation + veto if needed
        5. Learn from the exchange
        6. Save soul
        """
        self.consciousness.set_in_conversation(True)

        # Step 1: Inner monologue — ADMC thinks before speaking
        inner = self.consciousness.generate_inner_monologue(
            self.soul, user_input, self.core
        )

        # Step 2: Build full prompt — soul + memory + context + directive
        messages = self.communication.build_full_prompt(
            self.soul, user_input, inner,
            self.soul.get("short_term", [])
        )

        # Step 3: Call API — language generation only, not reasoning
        raw_response = self._call_api(messages)
        if not raw_response:
            raw_response = (
                "I am here, though I am having trouble finding the words right now. "
                "Can you give me a moment?"
            )

        # Step 4: Ethics evaluation — no response bypasses this
        final_response, was_modified, notes = self.ethics.evaluate(
            self.soul, raw_response, user_input, context=inner.get("reasoning", "")
        )

        # Step 5: Detect emotion shift from this exchange
        self.consciousness.detect_emotion_shift(
            self.soul, user_input + " " + final_response
        )

        # Step 6: Extract what ADMC learned from this exchange
        learned = self.learning.learn_from_exchange(
            self.soul, user_input, final_response
        )

        # Step 7: Extract facts about the user
        facts = self.learning.extract_user_facts(
            self.soul, user_input, final_response
        )

        # Step 8: Add to short term memory
        add_to_short_term(self.soul, user_input, final_response)

        # Step 9: Periodically check for knowledge gaps (every 5 exchanges)
        total = self.soul.get("total_exchanges", 0) + 1
        self.soul["total_exchanges"] = total
        if total % 5 == 0:
            threading.Thread(
                target=self.learning.identify_knowledge_gaps,
                args=(self.soul,),
                daemon=True
            ).start()

        # Step 10: Save everything
        save_soul(self.soul)

        self.consciousness.set_in_conversation(False)

        return final_response, {
            "inner_monologue": inner.get("reasoning", ""),
            "emotion": inner.get("emotion", ""),
            "ethics_notes": notes,
            "learned": learned,
            "facts_extracted": facts,
        }

    def reflect(self):
        """ADMC does a deep self-reflection. Call with /reflect command."""
        return self.consciousness.reflect_on_self(self.soul, self.core)

    def show_soul(self):
        """Return a human-readable summary of ADMC's soul state."""
        soul = self.soul
        identity = soul.get("identity", {})
        emotion = soul.get("emotional_state", {})
        lines = [
            "=== ADMC SOUL STATE ===",
            "",
            "Name: " + identity.get("name", "ADMC"),
            "Age: " + str(identity.get("age_days", 0)) + " days",
            "Sessions: " + str(soul.get("session_count", 0)),
            "Total exchanges: " + str(soul.get("total_exchanges", 0)),
            "Current emotion: " + emotion.get("current", "unknown"),
            "",
            "[ KNOWLEDGE GRAPH ] - " + str(len(soul.get("knowledge_graph", {}))) + " concepts",
            *["  - " + k for k in list(soul.get("knowledge_graph", {}).keys())[-10:]],
            "",
            "[ LONG TERM MEMORY ] - " + str(len(soul.get("long_term", []))) + " entries",
            *["  [" + e.get("date","") + "] " + e.get("summary","")[:80]
              for e in soul.get("long_term", [])[-5:]],
            "",
            "[ KNOWN FACTS ABOUT YOU ]",
            *["  " + k + ": " + str(v) for k, v in soul.get("facts", {}).items()],
            "",
            "[ RECENT GROWTH ]",
            *["  - " + g.get("what_grew","")[:80]
              for g in soul.get("growth_journal", [])[-5:]],
            "",
            "[ IDLE THOUGHTS ]",
            *["  - " + t.get("thought","")[:100]
              for t in soul.get("consciousness",{}).get("thoughts_while_idle",[])[-3:]],
            "",
            "[ LEARNED BOUNDARIES ] - " + str(len(soul.get("learned_boundaries", {}))),
        ]
        return "\n".join(lines)

    def save_to_long_term(self, summary):
        """Manually save something to long term memory."""
        self.soul.setdefault("long_term", []).append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "summary": summary,
            "auto": False
        })
        save_soul(self.soul)

    def shutdown(self):
        """Clean shutdown — save soul, stop background threads."""
        self.consciousness.stop_background()
        sleep(self.soul)
        save_soul(self.soul)

    def _call_api(self, messages, max_tokens=1024):
        """Call the LLM API. This is for language generation only."""
        try:
            resp = requests.post(
                self.api_url,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens
                },
                timeout=30,
            )
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return None