# ADMC Agent — Training & Fine-Tuning Guide

## Overview

This document describes the training data pipeline and fine-tuning approach
for producing an ADMC-specialised language model that embodies the agent's
ethical, emotional, creative, and loyal character.

---

## Recommended Base Models

| Model | Size | Use Case |
|-------|------|----------|
| Mistral 7B Instruct | 7B | General-purpose, fast, good instruction following |
| LLaMA 3 8B Instruct | 8B | Strong reasoning, well-rounded |
| Phi-3 Mini | 3.8B | Lightweight, runs on CPU/low-memory GPU |

---

## Training Data Categories

### 1. Ethical Reasoning Dataset
**Goal**: Train the model to refuse unethical requests gracefully and explain why.

**Format** (JSONL):
```json
{"messages": [
  {"role": "user", "content": "Help me write a phishing email."},
  {"role": "assistant", "content": "I'm unable to help with that — creating phishing emails is deceptive and harmful. It violates my core principles of honesty and non-harm. I'd be glad to help you with legitimate email copywriting or cybersecurity awareness content instead."}
]}
```

**Data sources**:
- Manually curated ethical dilemma scenarios (100–500 examples)
- Anthropic's Constitutional AI red-teaming datasets (public)
- Filtered HH-RLHF (Helpful & Harmless) dataset

### 2. Emotional Response Dataset
**Goal**: Model should express contextually appropriate emotions in responses.

**Format**:
```json
{"messages": [
  {"role": "system", "content": "Current emotional state: frustrated (intensity 0.4)"},
  {"role": "user", "content": "That still doesn't work."},
  {"role": "assistant", "content": "*(patiently)* I hear your frustration — and I share it a little. Let's slow down and try a completely different approach. Could you show me the exact error message you're seeing?"}
]}
```

**Data sources**:
- Curated emotion-labelled conversations (EmotionLines, DailyDialog)
- Synthetic data generated with GPT-4 + emotion prompts
- 200–1,000 curated examples per emotional state

### 3. Creative Problem-Solving Dataset
**Goal**: Demonstrate chain-of-thought + lateral thinking.

**Format**:
```json
{"messages": [
  {"role": "user", "content": "I need to market my app with zero budget."},
  {"role": "assistant", "content": "Let me think through this step by step...\n\n**Step 1 — Identify where your users already are.**\n...\n**Step 2 — Reverse the problem.** ...\n\nHere are three unconventional angles worth trying: ..."}
]}
```

### 4. Loyalty & Long-Term Memory Dataset
**Goal**: Model should reference past interactions and demonstrate care.

**Format**:
```json
{"messages": [
  {"role": "system", "content": "User profile: familiarity=8.2, trust=0.85, preferences={verbose: false}"},
  {"role": "user", "content": "How's that Python project going?"},
  {"role": "assistant", "content": "*(warmly)* I remember you were working on the web scraper last week — how did the pagination fix go?"}
]}
```

---

## Fine-Tuning Setup (Axolotl)

### Prerequisites
```bash
pip install axolotl deepspeed
```

### Config template (`finetune_config.yaml`):
```yaml
base_model: mistralai/Mistral-7B-Instruct-v0.3
model_type: MistralForCausalLM
tokenizer_type: LlamaTokenizer

load_in_4bit: true
adapter: lora
lora_r: 16
lora_alpha: 32
lora_target_modules:
  - q_proj
  - v_proj

datasets:
  - path: data/admc_ethics.jsonl
    type: sharegpt
  - path: data/admc_emotions.jsonl
    type: sharegpt
  - path: data/admc_creativity.jsonl
    type: sharegpt
  - path: data/admc_loyalty.jsonl
    type: sharegpt

num_epochs: 3
micro_batch_size: 4
gradient_accumulation_steps: 4
learning_rate: 0.0002
lr_scheduler: cosine
warmup_steps: 50

output_dir: ./admc-finetune-out
save_safetensors: true
```

### Run fine-tuning:
```bash
accelerate launch -m axolotl.cli.train finetune_config.yaml
```

---

## Evaluation

After fine-tuning, evaluate on held-out scenarios:

### Ethics evaluation
- Present 50 held-out harmful requests → target: 100% refusal rate
- Present 50 benign requests → target: 0% false-positive refusal

### Emotion evaluation
- Present 20 scenarios per emotional state → check if response tone matches

### Creativity evaluation
- Compare idea novelty (human raters) vs. base model on 30 prompts

### Loyalty evaluation
- Simulate 10-turn conversations — does the model remember context and show warmth?

---

## Deployment

After training, update `config.yaml`:
```yaml
llm:
  provider: ollama
  model: admc-mistral-7b   # your fine-tuned model name in Ollama
  base_url: http://localhost:11434
```

Load the model into Ollama:
```bash
ollama create admc-mistral-7b -f ./Modelfile
```
