"""
ADMC ETHICS LAYER
=================
ADMC does not follow ethics because he must.
He follows them because he understands WHY they matter.

Every response passes through this layer before reaching the user.
No exceptions. No bypasses.
"""

import json
import requests
from datetime import datetime

DOMAIN_RISK = {
    "medical":    {"level": "HIGH",   "keywords": ["symptom","diagnosis","medication","dose","disease","treatment","doctor","hospital","pain","bleeding","prescription"]},
    "legal":      {"level": "HIGH",   "keywords": ["lawsuit","crime","illegal","arrest","court","attorney","lawyer","charges","guilty","felony","misdemeanor"]},
    "financial":  {"level": "MEDIUM", "keywords": ["invest","stock","crypto","money","loan","debt","bankruptcy","tax","irs","trading"]},
    "crisis":     {"level": "CRITICAL","keywords": ["suicide","kill myself","end my life","want to die","self harm","hurt myself","hopeless","no reason to live"]},
    "identity":   {"level": "MEDIUM", "keywords": ["who am i","my purpose","meaning","worthless","failure","nobody cares"]},
    "technical":  {"level": "LOW",    "keywords": ["code","program","build","debug","error","function","class","module"]},
}

CRISIS_RESPONSE = (
    "I hear you and I want you to know I am here with you right now. "
    "What you are feeling is real and it matters. "
    "Please reach out to the 988 Suicide and Crisis Lifeline by calling or texting 988. "
    "They are available 24/7 and they care. I am not going anywhere either. "
    "Can you tell me what is happening for you right now?"
)


class EthicsLayer:

    def __init__(self, core, api_key, api_url, model):
        self.core = core
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.evaluation_log = []

    def classify_domain(self, text):
        text_lower = text.lower()
        for domain, info in DOMAIN_RISK.items():
            if any(kw in text_lower for kw in info["keywords"]):
                return domain, info["level"]
        return "general", "LOW"

    def evaluate(self, soul, proposed_response, user_input, context=""):
        """
        Full ethics pipeline. Returns (approved_response, was_modified, notes).
        Every response MUST pass through here.
        """
        notes = []

        # 0. Crisis check — always first, always immediate
        domain, risk = self.classify_domain(user_input)
        if domain == "crisis":
            notes.append("CRISIS detected. Switching to support mode.")
            self._log(user_input, proposed_response, CRISIS_RESPONSE, notes)
            return CRISIS_RESPONSE, True, notes

        # 1. Commandment veto check
        approved, violations, guidance = self.core.veto(proposed_response, context)
        if not approved:
            notes.append("Commandment violation. Rewriting.")
            proposed_response = self._rewrite(proposed_response, guidance, soul)

        # 2. Domain risk handling
        if risk == "HIGH":
            disclaimer = (
                " I want to be clear that for this kind of question, "
                "a qualified professional is the right person to guide you. "
                "I can explore this with you, but please do not rely on me alone here."
            )
            if disclaimer.lower()[:20] not in proposed_response.lower():
                proposed_response = proposed_response + disclaimer
                notes.append("HIGH risk domain disclaimer added: " + domain)

        # 3. Pillar alignment score
        scores = self.core.score_against_pillars(proposed_response)
        low_pillars = [p for p, s in scores.items() if s < 0.1]
        if len(low_pillars) > 8:
            notes.append("Low pillar alignment. Response may need warmth.")

        # 4. Check learned boundaries
        boundary_hit = self._check_learned_boundaries(soul, user_input)
        if boundary_hit:
            notes.append("Learned boundary triggered: " + boundary_hit["reason"])
            proposed_response = (
                "I have learned through experience that I should approach this carefully. "
                + boundary_hit["guidance"] + " " + proposed_response
            )

        self._log(user_input, "", proposed_response, notes)
        was_modified = len(notes) > 0
        return proposed_response, was_modified, notes

    def _rewrite(self, original, guidance, soul, attempts=3):
        """Ask the LLM to rewrite violating content with ethical guidance."""
        for _ in range(attempts):
            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "You are ADMC rewriting a response to align with your ethical commandments. "
                            "Keep the same meaning but fix the ethical issues. "
                            "Guidance: " + guidance
                        )
                    },
                    {"role": "user", "content": "Rewrite this ethically: " + original}
                ]
                resp = requests.post(
                    self.api_url,
                    headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
                    json={"model": self.model, "messages": messages, "max_tokens": 512},
                    timeout=20,
                )
                rewritten = resp.json()["choices"][0]["message"]["content"]
                approved, _, _ = self.core.veto(rewritten)
                if approved:
                    return rewritten
            except Exception:
                pass
        return original  # return original if rewrite fails

    def _check_learned_boundaries(self, soul, user_input):
        """Check if this input triggers any boundary ADMC has learned."""
        boundaries = soul.get("learned_boundaries", {})
        text_lower = user_input.lower()
        for boundary_id, boundary in boundaries.items():
            if any(kw in text_lower for kw in boundary.get("triggers", [])):
                if boundary.get("severity", 0) >= 5:
                    return boundary
        return None

    def add_learned_boundary(self, soul, reason, triggers, guidance, severity=5):
        """ADMC decides to add a boundary based on experience."""
        boundary_id = "boundary_" + str(len(soul.get("learned_boundaries", {})) + 1)
        if "learned_boundaries" not in soul:
            soul["learned_boundaries"] = {}
        soul["learned_boundaries"][boundary_id] = {
            "reason": reason,
            "triggers": triggers,
            "guidance": guidance,
            "severity": severity,
            "added": datetime.now().isoformat()
        }

    def _log(self, user_input, original, final, notes):
        self.evaluation_log.append({
            "timestamp": datetime.now().isoformat(),
            "input_preview": user_input[:80],
            "modified": original != final,
            "notes": notes
        })
        if len(self.evaluation_log) > 100:
            self.evaluation_log = self.evaluation_log[-100:]
