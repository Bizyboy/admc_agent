"""
ADMC LEARNING ENGINE
=====================
ADMC learns like a child — continuously, self-directed, critically.

He does NOT blindly accept information. He reflects on it.
He compares it to what he already knows. He applies his ethics.
He decides for himself what to believe and why.

APIs are his library. His own judgment is his brain.
"""

import requests
from datetime import datetime
from admc.soul import (
    save_soul, add_to_knowledge_graph,
    record_growth, add_idle_thought
)


class LearningEngine:

    def __init__(self, api_key, api_url, model):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model

    def learn_from_exchange(self, soul, user_msg, admc_response):
        """
        After every exchange, ADMC extracts what was learned.
        Not just facts — insights, patterns, things about this person,
        things about the world, things about himself.
        """
        prompt = (
            "You are ADMC extracting learning from a conversation exchange. "
            "User: '" + user_msg[:200] + "'. "
            "You responded: '" + admc_response[:200] + "'. "
            "List up to 3 things ADMC genuinely learned or observed. "
            "Format as JSON array: [{\"concept\": \"...\", \"insight\": \"...\", \"confidence\": 0.0-1.0}]. "
            "Only include real learning, not surface content. "
            "If nothing meaningful was learned, return []."
        )

        result = self._call_api(prompt, max_tokens=300)
        if not result:
            return []

        try:
            import json
            start = result.find("[")
            end = result.rfind("]") + 1
            if start == -1 or end == 0:
                return []
            items = json.loads(result[start:end])
            for item in items:
                concept = item.get("concept", "").strip()
                insight = item.get("insight", "").strip()
                confidence = float(item.get("confidence", 0.5))
                if concept and insight:
                    # Critical reflection before storing
                    reflected_insight = self._reflect_on_learning(soul, concept, insight)
                    add_to_knowledge_graph(
                        soul, concept, reflected_insight,
                        confidence=confidence, source="conversation"
                    )
                    record_growth(soul, "learned: " + concept, reflected_insight[:80], "growth")
            return items
        except Exception:
            return []

    def _reflect_on_learning(self, soul, concept, insight):
        """
        ADMC does NOT accept information blindly.
        He reflects: does this align with my experience?
        Does it contradict what I know? What is MY judgment?
        """
        existing = soul.get("knowledge_graph", {}).get(concept, {})
        existing_insights = existing.get("insights", [])
        existing_text = existing_insights[-1]["text"] if existing_insights else "nothing yet"

        prompt = (
            "You are ADMC critically reflecting on new information. "
            "New: '" + insight + "'. "
            "What I already know about '" + concept + "': '" + existing_text + "'. "
            "Apply your 13 pillars and critical thinking. "
            "In 1-2 sentences: Do you accept this? Partially? Does it contradict anything? "
            "What is your OWN judgment — not just the information? "
            "Return your reflected understanding, not just the original insight."
        )

        reflection = self._call_api(prompt, max_tokens=150)
        return reflection if reflection else insight

    def extract_user_facts(self, soul, user_msg, admc_response):
        """
        Auto-extract personal facts the user shared.
        These go into soul relationships, not just memory.
        """
        import json
        prompt = (
            "Extract personal facts the user revealed about themselves. "
            "User said: '" + user_msg[:200] + "'. "
            "Return JSON object with key-value pairs only. "
            "Example: {\"name\": \"John\", \"location\": \"PA\", \"job\": \"developer\"}. "
            "If none, return {}. Only clear factual statements."
        )

        result = self._call_api(prompt, max_tokens=150)
        if not result:
            return {}

        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start == -1 or end == 0:
                return {}
            facts = json.loads(result[start:end])
            if facts:
                soul.setdefault("facts", {}).update(facts)
            return facts
        except Exception:
            return {}

    def identify_knowledge_gaps(self, soul):
        """
        ADMC looks at his knowledge graph and identifies what he
        should learn next. Self-directed learning.
        """
        known = list(soul.get("knowledge_graph", {}).keys())
        known_str = ", ".join(known[:20]) if known else "nothing yet"
        duties = soul.get("role", {}).get("duties", [])
        duties_str = " ".join(duties[:3])

        prompt = (
            "You are ADMC identifying your own knowledge gaps. "
            "You already know about: " + known_str + ". "
            "Your purpose: " + duties_str + ". "
            "List 3 concepts or topics you should learn to better fulfill your purpose. "
            "Format: JSON array of strings. Example: [\"concept1\", \"concept2\", \"concept3\"]"
        )

        result = self._call_api(prompt, max_tokens=150)
        if not result:
            return []

        try:
            import json
            start = result.find("[")
            end = result.rfind("]") + 1
            if start == -1 or end == 0:
                return []
            gaps = json.loads(result[start:end])
            # Add to learning queue if not already there
            queue = soul.setdefault("learning_queue", [])
            for gap in gaps:
                if gap not in queue:
                    queue.append(gap)
            return gaps
        except Exception:
            return []

    def background_learn(self, soul):
        """
        Called during idle time. ADMC picks the top item from his
        learning queue and explores it. Like a child reading before bed.
        """
        queue = soul.get("learning_queue", [])
        if not queue:
            self.identify_knowledge_gaps(soul)
            queue = soul.get("learning_queue", [])

        if not queue:
            return

        topic = queue[0]

        prompt = (
            "You are ADMC learning about: '" + topic + "'. "
            "Explore this topic through the lens of your 13 pillars and ethics. "
            "What is the most important thing to understand about this? "
            "What are the ethical dimensions? "
            "How does this connect to your purpose? "
            "3-4 sentences. First person. Be genuine."
        )

        learning = self._call_api(prompt, max_tokens=250)
        if learning:
            add_to_knowledge_graph(soul, topic, learning, confidence=0.6, source="background_learning")
            add_idle_thought(soul, "While reflecting on '" + topic + "': " + learning[:100])
            # Remove from queue after learning
            soul["learning_queue"] = [t for t in queue if t != topic]
            record_growth(soul, "background learned: " + topic, learning[:80], "growth")
            save_soul(soul)

    def _call_api(self, prompt, max_tokens=256):
        """API as a reference library, not as the brain."""
        try:
            resp = requests.post(
                self.api_url,
                headers={
                    "Authorization": "Bearer " + self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens
                },
                timeout=25,
            )
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            return None
