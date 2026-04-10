import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
except ImportError:
    os.system("pip install requests -q")
    import requests

from memory import (
    load_memory, save_memory, build_system_prompt, build_message_history,
    add_to_short_term, save_to_long_term, clear_short_term,
    add_knowledge, add_duty, show_memory_summary
)

API_KEY = os.environ.get("XAI_API_KEY", "")
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-3-mini"

if not API_KEY:
    print("ERROR: XAI_API_KEY not set. Add it to a .env file.")
    sys.exit(1)

memory = load_memory()

print("")
print("ADMC is online.")
print("Short term: " + str(len(memory["short_term"])) + " recent exchanges loaded.")
print("Long term:  " + str(len(memory["long_term"])) + " saved memories.")
print("")
print("Commands: memory | save <summary> | learn <fact> | duty <task> | forget | quit")
print("")


def ask_grok(memory, user_input):
    system_prompt = build_system_prompt(memory)
    messages = build_message_history(memory, system_prompt)
    messages.append({"role": "user", "content": user_input})

    resp = requests.post(
        API_URL,
        headers={
            "Authorization": "Bearer " + API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": messages,
            "max_tokens": 1024,
        },
        timeout=30,
    )
    data = resp.json()
    return data["choices"][0]["message"]["content"]


while True:
    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        save_memory(memory)
        print("")
        print("ADMC: Memory saved. Take care. Until next time.")
        break

    if not user_input:
        continue

    # --- Commands ---

    if user_input.lower() in ("quit", "exit", "bye"):
        save_memory(memory)
        print("ADMC: Memory saved. Take care. Until next time.")
        break

    if user_input.lower() == "memory":
        show_memory_summary(memory)
        continue

    if user_input.lower().startswith("save "):
        summary = user_input[5:].strip()
        if summary:
            save_to_long_term(memory, summary)
        else:
            print("ADMC: Usage: save <summary of what to remember long term>")
        print("")
        continue

    if user_input.lower().startswith("learn "):
        fact = user_input[6:].strip()
        if fact:
            add_knowledge(memory, fact)
            print("ADMC: Got it. Added to my knowledge base.")
        else:
            print("ADMC: Usage: learn <fact to add to knowledge base>")
        print("")
        continue

    if user_input.lower().startswith("duty "):
        duty = user_input[5:].strip()
        if duty:
            add_duty(memory, duty)
            print("ADMC: Understood. Added to my duties.")
        else:
            print("ADMC: Usage: duty <new duty or responsibility>")
        print("")
        continue

    if user_input.lower() == "forget":
        clear_short_term(memory)
        print("ADMC: Short term memory cleared. Long term memory and knowledge base kept.")
        print("")
        continue

    # --- Normal conversation ---

    try:
        reply = ask_grok(memory, user_input)
    except Exception as e:
        print("")
        print("ADMC: Error - " + str(e))
        print("")
        continue

    add_to_short_term(memory, user_input, reply)
    save_memory(memory)

    print("")
    print("ADMC: " + reply)
    print("")
