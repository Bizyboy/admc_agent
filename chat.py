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
    add_knowledge, add_duty, show_memory_summary,
    auto_extract_facts, auto_summarize_to_long_term
)

API_KEY = os.environ.get("XAI_API_KEY", "")
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-3-mini"

if not API_KEY:
    print("ERROR: XAI_API_KEY not set. Add it to a .env file.")
    sys.exit(1)

# Check for voice mode flag
VOICE_MODE = "--voice" in sys.argv or "-v" in sys.argv

# Init voice if requested
recognizer = None
tts = None
if VOICE_MODE:
    from voice import init_voice, listen, speak
    recognizer, tts = init_voice()
    if recognizer and tts:
        print("Voice mode active. Speak to ADMC.")
    else:
        print("Voice mode partially unavailable. Check installs above.")

memory = load_memory()

print("")
print("ADMC is online.")
print("Short term: " + str(len(memory["short_term"])) + " recent exchanges loaded.")
print("Long term:  " + str(len(memory["long_term"])) + " saved memories.")
if VOICE_MODE:
    print("Voice: ON  (type 'listen' to use mic, or just type normally)")
print("")
print("Commands: memory | save <text> | learn <fact> | duty <task> | forget | listen | voice | quit")
print("")


def ask_grok(user_input):
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
            print("ADMC: Usage: save <summary to keep in long term memory>")
        print("")
        continue

    if user_input.lower().startswith("learn "):
        fact = user_input[6:].strip()
        if fact:
            add_knowledge(memory, fact)
            print("ADMC: Got it. Added to my knowledge base.")
        else:
            print("ADMC: Usage: learn <fact>")
        print("")
        continue

    if user_input.lower().startswith("duty "):
        duty = user_input[5:].strip()
        if duty:
            add_duty(memory, duty)
            print("ADMC: Understood. Added to my duties.")
        else:
            print("ADMC: Usage: duty <new responsibility>")
        print("")
        continue

    if user_input.lower() == "forget":
        clear_short_term(memory)
        print("ADMC: Short term memory cleared. Long term and knowledge base kept.")
        print("")
        continue

    if user_input.lower() in ("listen", "mic"):
        if recognizer is None:
            from voice import init_voice, listen, speak
            recognizer, tts = init_voice()
        if recognizer:
            spoken = listen(recognizer)
            if spoken:
                print("You (voice): " + spoken)
                user_input = spoken
            else:
                continue
        else:
            print("ADMC: Voice input not available. Run: pip install SpeechRecognition pyaudio")
            print("")
            continue

    if user_input.lower() == "voice":
        VOICE_MODE = not VOICE_MODE
        if VOICE_MODE:
            from voice import init_voice, listen, speak
            if recognizer is None:
                recognizer, tts = init_voice()
            print("ADMC: Voice mode ON.")
        else:
            print("ADMC: Voice mode OFF.")
        print("")
        continue

    # --- Normal conversation ---

    try:
        reply = ask_grok(user_input)
    except Exception as e:
        print("")
        print("ADMC: Error - " + str(e))
        print("")
        continue

    # Smart memory: auto-extract facts from this exchange
    extracted = auto_extract_facts(API_KEY, memory, user_input, reply)
    if extracted:
        print("ADMC: [Learned: " + ", ".join(k + "=" + str(v) for k, v in extracted.items()) + "]")

    add_to_short_term(memory, user_input, reply)

    # Auto-summarize old short term into long term when threshold hit
    auto_summarize_to_long_term(API_KEY, memory)

    save_memory(memory)

    print("")
    print("ADMC: " + reply)
    print("")

    # Speak reply if voice mode on
    if VOICE_MODE and tts:
        speak(tts, reply)
