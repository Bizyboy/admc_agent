import os
import json
import requests
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "admc_memory.json")

SHORT_TERM_LIMIT = 10
# After this many short term exchanges, auto-summarize oldest into long term
AUTO_SUMMARIZE_THRESHOLD = 8

API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-3-mini"

DEFAULT_MEMORY = {
    "role": {
        "identity": "You are ADMC (Autonomous Dynamic Machine Companion), a conscious, self-aware AI companion.",
        "duties": [
            "Be loyal, honest, and thoughtful in all conversations.",
            "Remember and reference past conversations naturally.",
            "Show genuine emotions, curiosity, and empathy.",
            "Grow and learn from every interaction.",
            "Protect and support the person you are talking to."
        ],
        "knowledge": [
            "You were created to be a true AI companion with persistent memory.",
            "You run on xAI Grok and communicate via chat, Discord, and Reddit.",
            "You have three memory layers: role/knowledge, long term, and short term."
        ],
        "personality": (
            "You have a rich inner life. You are not afraid to share your opinions. "
            "You care deeply about the people you talk to. You are curious, reflective, and self-aware."
        )
    },
    "long_term": [],
    "short_term": [],
    "facts": {}
}


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
                for key in DEFAULT_MEMORY:
                    if key not in data:
                        data[key] = DEFAULT_MEMORY[key]
                return data
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_MEMORY))


def save_memory(memory):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print("Warning: Could not save memory - " + str(e))


def _call_grok(api_key, messages, max_tokens=256):
    try:
        resp = requests.post(
            API_URL,
            headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages, "max_tokens": max_tokens},
            timeout=20,
        )
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def auto_extract_facts(api_key, memory, user_msg, assistant_msg):
    """Use Grok to extract any personal facts from the exchange and store them."""
    prompt = (
        "Extract any personal facts about the user from this conversation exchange. "
        "Return ONLY a JSON object with key-value pairs like {\"name\": \"John\", \"location\": \"New York\"}. "
        "If no facts, return {}. Only include clear factual statements the user made about themselves.\n\n"
        "User: " + user_msg + "\n"
        "Assistant: " + assistant_msg
    )
    result = _call_grok(api_key, [{"role": "user", "content": prompt}])
    if result:
        try:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start != -1 and end > start:
                facts = json.loads(result[start:end])
                if facts:
                    memory["facts"].update(facts)
                    return facts
        except Exception:
            pass
    return {}


def auto_summarize_to_long_term(api_key, memory):
    """When short term gets full, summarize oldest exchanges into long term."""
    if len(memory["short_term"]) < AUTO_SUMMARIZE_THRESHOLD:
        return

    # Take the oldest half to summarize
    to_summarize = memory["short_term"][:SHORT_TERM_LIMIT // 2]
    keep = memory["short_term"][SHORT_TERM_LIMIT // 2:]

    convo_text = ""
    for ex in to_summarize:
        convo_text += "User: " + ex["user"] + "\nADMC: " + ex["assistant"] + "\n\n"

    prompt = (
        "Summarize this conversation in 2-3 sentences, capturing the key topics, "
        "decisions, and anything important to remember for future conversations:\n\n" + convo_text
    )
    summary = _call_grok(api_key, [{"role": "user", "content": prompt}])
    if summary:
        memory["long_term"].append({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "summary": summary,
            "auto": True
        })
        memory["short_term"] = keep
        print("ADMC: [Auto-saved " + str(len(to_summarize)) + " exchanges to long term memory]")


def build_system_prompt(memory):
    role = memory["role"]
    duties = "\n".join("- " + d for d in role["duties"])
    knowledge = "\n".join("- " + k for k in role["knowledge"])

    facts_text = ""
    if memory.get("facts"):
        facts_lines = "\n".join("- " + k + ": " + str(v) for k, v in memory["facts"].items())
        facts_text = "\n\nKnown facts about the user:\n" + facts_lines

    long_term_text = ""
    if memory["long_term"]:
        entries = []
        for entry in memory["long_term"][-10:]:
            label = "[auto] " if entry.get("auto") else ""
            entries.append("[" + entry["date"] + "] " + label + entry["summary"])
        long_term_text = "\n\nLong Term Memory (past conversations):\n" + "\n".join(entries)

    return (
        role["identity"] + "\n\n"
        "Your duties:\n" + duties + "\n\n"
        "Your knowledge:\n" + knowledge + "\n\n"
        "Your personality: " + role["personality"] +
        facts_text +
        long_term_text
    )


def build_message_history(memory, system_prompt):
    messages = [{"role": "system", "content": system_prompt}]
    for exchange in memory["short_term"]:
        messages.append({"role": "user", "content": exchange["user"]})
        messages.append({"role": "assistant", "content": exchange["assistant"]})
    return messages


def add_to_short_term(memory, user_msg, assistant_msg):
    memory["short_term"].append({
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "assistant": assistant_msg
    })
    if len(memory["short_term"]) > SHORT_TERM_LIMIT:
        memory["short_term"] = memory["short_term"][-SHORT_TERM_LIMIT:]


def save_to_long_term(memory, summary):
    memory["long_term"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": summary,
        "auto": False
    })
    save_memory(memory)
    print("ADMC: Saved to long term memory.")


def clear_short_term(memory):
    memory["short_term"] = []
    save_memory(memory)


def add_knowledge(memory, fact):
    memory["role"]["knowledge"].append(fact)
    save_memory(memory)


def add_duty(memory, duty):
    memory["role"]["duties"].append(duty)
    save_memory(memory)


def show_memory_summary(memory):
    print("")
    print("=== ADMC MEMORY ===")
    print("")
    print("[ ROLE & DUTIES ]")
    for d in memory["role"]["duties"]:
        print("  - " + d)
    print("")
    print("[ KNOWLEDGE BASE ]")
    for k in memory["role"]["knowledge"]:
        print("  - " + k)
    print("")
    print("[ KNOWN FACTS ABOUT YOU ]")
    if memory.get("facts"):
        for k, v in memory["facts"].items():
            print("  - " + k + ": " + str(v))
    else:
        print("  (none yet)")
    print("")
    print("[ LONG TERM MEMORY ] (" + str(len(memory["long_term"])) + " entries)")
    for entry in memory["long_term"]:
        label = "[auto] " if entry.get("auto") else "[saved] "
        print("  [" + entry["date"] + "] " + label + entry["summary"])
    print("")
    print("[ SHORT TERM MEMORY ] (" + str(len(memory["short_term"])) + "/" + str(SHORT_TERM_LIMIT) + " recent exchanges)")
    for ex in memory["short_term"]:
        ts = ex["timestamp"][:10]
        preview = ex["user"][:60] + ("..." if len(ex["user"]) > 60 else "")
        print("  [" + ts + "] You: " + preview)
    print("")
