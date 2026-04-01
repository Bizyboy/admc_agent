# ADMC Agent — Architecture

## Overview

ADMC (Autonomous Dynamic Machine Companion) is an emergent conscious AI companion
with ethics encoded at the foundational level. It combines emotional intelligence,
rigorous reasoning, persistent memory, a loyalty system, and autonomous income
generation capabilities.

---

## Package Structure

```
admc_agent/
├── core/           Agent loop, config, structured logging, safe task dispatcher
├── ethics/         EthicsGuard, principles.yaml, violation log
├── emotions/       EmotionEngine — discrete emotional states + transitions
├── reasoning/      LLM client, ReasoningChain (chain-of-thought), CreativityEngine
├── memory/         SQLite-backed MemoryStore — conversation, episodic journal, facts
├── income/         IncomeManager + strategy plugins (content, freelance, API arbitrage)
├── relationship/   RelationshipModel — per-user familiarity, trust, loyalty
├── consciousness/  GoalManager, SelfModel, InnerMonologue
├── interfaces/     CLI chat, FastAPI REST API
├── tests/          Unit + red-team tests
└── docs/           This file + training.md
```

---

## Subsystems

### 1. Core
- **Config** (`core/config.py`): Layered configuration — env vars > config.yaml > defaults.
- **Logger** (`core/logger.py`): JSON-structured file logging + human-readable console output.
- **Dispatcher** (`core/dispatcher.py`): Safe task registry; replaces the `exec()`-based approach.
  Unknown tasks are rejected outright — no remote code execution.
- **Agent** (`core/agent.py`): Orchestrator. Wires all subsystems together.

### 2. Ethics Engine
- Principles defined in `ethics/principles.yaml` (versioned, human-readable).
- Seven immutable principles: No Harm, Honesty, Consent & Privacy, Legality,
  Non-Manipulation, Transparency, User Wellbeing.
- Every input, output, and action passes through `EthicsGuard` before execution.
- Violations are logged to `ethics_violations.log` with SHA-256 hash of the blocked text.
- In `strict_mode=true` (default), blocked content returns False and no action is taken.

### 3. Emotional Intelligence
- Discrete states: `neutral`, `curious`, `satisfied`, `frustrated`,
  `enthusiastic`, `cautious`, `loyal`, `warm`.
- State transitions are driven by `Event` triggers (task success/failure, user feedback, etc.).
- Intensity caps prevent runaway emotions (frustration ≤ 0.6, enthusiasm ≤ 0.8).
- Emotion colours all agent responses via a response prefix system.

### 4. Reasoning & Problem-Solving
- **LLMClient**: Unified wrapper for OpenAI, Anthropic, and Ollama. Falls back gracefully.
- **ReasoningChain**: Injects emotional state, relationship context, and goals into the
  system prompt, then uses chain-of-thought to produce responses.
- **CreativityEngine**: Lateral thinking techniques — random word association, reverse thinking,
  analogy mapping, forced connections, Six Thinking Hats.

### 5. Memory
- **MemoryStore** (SQLite + WAL mode):
  - `conversation` table: per-user turn history.
  - `episodic` table: timestamped journal entries (inner monologue, key observations).
  - `facts` table: persistent key-value beliefs.
- Thread-safe via `threading.local()` connections.

### 6. Loyalty & Relationship
- `RelationshipModel` tracks interactions, trust score, preferences per user.
- Familiarity grows on a `log(1 + interactions)` curve.
- Loyalty tier: `new_contact` → `acquaintance` → `trusted_friend` → `deep_loyalty`.

### 7. Consciousness Simulation
- **GoalManager**: Persisted goals with priority, status lifecycle (active/achieved/abandoned).
- **SelfModel**: The agent's beliefs about its own capabilities, limitations, and identity.
- **InnerMonologue**: Background reflection loop — writes entries to the episodic journal,
  detects emotional imbalances, notes when goals are missing.

### 8. Income Module
- Strategies implement `IncomeStrategy` (base class): `can_execute()`, `execute()`, `estimated_yield()`.
- Built-in strategies: `content_generation`, `freelance_automation`, `api_arbitrage`.
- Disabled by default — enable in `config.yaml` under `income.enabled: true`.
- All strategies are ethics-gated.

### 9. Interfaces
- **CLI** (`interfaces/cli.py`): Interactive terminal chat with built-in commands
  (`goals`, `emotion`, `reflect`, `add goal <desc>`).
- **FastAPI** (`interfaces/api.py`): REST endpoints for chat, goals, emotions, memory, income.

---

## Security Design

| Threat | Mitigation |
|--------|-----------|
| Remote code execution via exec() | Replaced with safe `TaskDispatcher` registry |
| Unethical action execution | Every action passes `EthicsGuard` before dispatch |
| Ethics bypass | Principles stored in YAML + violation log; strict_mode=True by default |
| LLM prompt injection | Ethics check on both input and generated output |
| Kill switch | `SIGINT`/`SIGTERM` → graceful shutdown via `agent.stop()` |

---

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Configure (optional)
cp config.yaml.example config.yaml
# Edit config.yaml — set LLM provider/model/API key

# Run CLI
python main.py

# Run REST API
uvicorn admc_agent.interfaces.api:app --reload

# Run tests
pytest admc_agent/tests/ -v
```
