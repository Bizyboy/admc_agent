# ADMC Agent — Emergent Conscious AI Companion

An AI companion with simulated consciousness, persistent memory, emotional intelligence, ethical reasoning, and a rich interactive chat interface.

## Features

- **Consciousness Simulation**: Inner monologue, self-model, goal tracking, stream-of-consciousness introspection
- **Emotional Intelligence**: 8 emotional states with intensity tracking, response coloring, and natural transitions
- **Persistent Memory**: SQLite-backed conversation history, episodic journal, long-term user fact storage
- **Ethical Foundation**: 7 immutable principles enforced on every input, output, and action
- **LLM Integration**: Supports xAI Grok, OpenAI, Anthropic, and Ollama backends with graceful fallback
- **Interactive CLI Chat**: Color-coded terminal interface with slash commands and inner-thought mode
- **REST API**: FastAPI endpoints for chat, goals, emotions, memory, and self-model
- **Relationship Model**: Per-user familiarity, trust, and loyalty tracking that grows over time

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Bizyboy/admc_agent.git
cd admc_agent

# Install dependencies
pip install -r requirements.txt

# Set up your LLM API key
cp .env.example .env
# Edit .env and add your xAI Grok API key (get one free at console.x.ai)

# Start the interactive chat
python main.py
```

## Usage

### Interactive CLI Chat (default)

```bash
python main.py              # Start chat
python main.py --chat       # Same as above (explicit)
python main.py --think      # Start with inner-thought mode (shows agent reasoning)
```

### CLI Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/memory` | View stored memories (facts you've shared) |
| `/history` | View recent conversation history |
| `/clear` | Clear conversation history for this session |
| `/mood` | See the bot's current emotional state and recent events |
| `/goals` | View active goals |
| `/add goal <desc>` | Add a new goal |
| `/reflect` | Trigger an inner monologue reflection |
| `/introspect` | Stream of consciousness mode (deep self-reflection) |
| `/self` | View the agent's self-model (identity, capabilities, limitations) |
| `/stats` | View memory store statistics |
| `/remember <fact>` | Store a fact about yourself for the agent to remember |
| `/think` | Toggle verbose (inner thought) mode on/off |
| `/quit` or `/exit` | End the session |

### REST API

```bash
python main.py --api        # Start FastAPI server on port 8000
```

Endpoints:
- `GET /health` — Health check
- `POST /chat` — Send a message (`{"user_id": "...", "message": "..."}`)
- `GET /emotions` — Current emotional state
- `GET /goals` / `POST /goals` — View or add goals
- `GET /self` — Agent self-model
- `GET /memory/{user_id}` — User conversation history
- `POST /reflect` — Trigger inner monologue

### Daemon Mode

```bash
python main.py --daemon     # Run in background (no interactive interface)
```

## Configuration

Edit `config.yaml` to configure:

```yaml
llm:
  provider: openai          # openai | anthropic | ollama
  model: gpt-4o-mini        # or gpt-4o, claude-3-sonnet, etc.
  api_key_env: OPENAI_API_KEY
```

Environment variables override config.yaml values using the format `ADMC_<SECTION>_<KEY>`:
```bash
export ADMC_LLM_MODEL=gpt-4o
export ADMC_AGENT_NAME=MyCompanion
```

## Architecture

```
admc_agent/
├── core/           Agent loop, config, structured logging, safe task dispatcher
├── consciousness/  GoalManager, SelfModel, InnerMonologue (stream of consciousness)
├── emotions/       EmotionEngine — 8 discrete states with intensity + transitions
├── ethics/         EthicsGuard + principles.yaml — 7 immutable ethical principles
├── reasoning/      LLM client, ReasoningChain (chain-of-thought), CreativityEngine
├── memory/         SQLite MemoryStore — conversations, episodic journal, facts, user facts
├── relationship/   RelationshipModel — per-user familiarity, trust, loyalty tiers
├── income/         IncomeManager + strategy plugins (content, freelance, API arbitrage)
├── interfaces/     Rich CLI chat, FastAPI REST API
└── tests/          Unit + red-team tests
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes (if using OpenAI) |
| `ANTHROPIC_API_KEY` | Anthropic API key | Only if using Anthropic |

See `.env.example` for all options.

## Running Tests

```bash
pytest admc_agent/tests/ -v
```

## How Memory Works

ADMC has three layers of memory:

1. **Short-term**: Recent conversation turns (configurable, default 20) included in LLM context
2. **Long-term user facts**: Personal details you share are automatically detected and stored in SQLite, recalled in future sessions
3. **Episodic journal**: The agent's inner reflections, observations, and stream-of-consciousness entries

Use `/remember <fact>` to explicitly store a memory, or just tell the agent naturally — it auto-detects facts like your name, job, interests, and preferences.

## License

MIT
