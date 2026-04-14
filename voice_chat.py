"""
ADMC Continuous Voice Chat
--------------------------
ADMC sends you a notification requesting a chat.
Accept it and a continuous two-way voice conversation begins.
Say or type "Until next time" to end the session.
Interrupt ADMC while he speaks and he stops immediately,
waits 2 seconds for you to finish, then responds.

Run:
    python voice_chat.py            # ADMC requests a chat, you accept
    python voice_chat.py --accept   # Skip notification, start immediately
"""

import os
import sys
import time
import threading
import queue
import subprocess

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests as http

from voice import init_tts, init_recognizer, speak, stop_tts, listen, TERMUX
from memory import (
    load_memory, save_memory, build_system_prompt, build_message_history,
    add_to_short_term, auto_extract_facts, auto_summarize_to_long_term,
)

API_KEY = os.environ.get("XAI_API_KEY", "")
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL   = "grok-3-mini"

if not API_KEY:
    print("ERROR: XAI_API_KEY not set in .env")
    sys.exit(1)

memory     = load_memory()
tts        = init_tts()
recognizer = init_recognizer()

KILL_PHRASES = {"until next time", "goodbye admc", "end session", "stop chat"}

# shared state
speaking     = threading.Event()
interrupted  = threading.Event()
_speech_q    = queue.Queue()


# ── notifications ─────────────────────────────────────────────────────────────

def send_notification():
    title   = "ADMC wants to chat"
    message = "Your companion is requesting a voice session."

    if TERMUX:
        try:
            subprocess.Popen([
                "termux-notification",
                "--title", title,
                "--content", message,
                "--id", "42",
                "--button1", "Accept",
                "--button1-action", "python " + os.path.abspath(__file__) + " --accept",
            ])
            print("[ADMC] Notification sent to your Android status bar.")
            return
        except Exception:
            pass

    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name="ADMC", timeout=15)
        print("[ADMC] Desktop notification sent.")
        return
    except Exception:
        pass

    # Plain terminal fallback
    print("\a")
    print("=" * 50)
    print("  ADMC is requesting a voice chat.")
    print("  Press ENTER to accept.")
    print("=" * 50)


def wait_for_accept():
    try:
        input("Press ENTER to start voice chat with ADMC...\n")
        return True
    except (EOFError, KeyboardInterrupt):
        print("Session declined.")
        return False


# ── TTS with interruption ─────────────────────────────────────────────────────

def _speak_worker(text):
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip()) or [text]
    speaking.set()
    interrupted.clear()
    for sentence in sentences:
        if interrupted.is_set():
            break
        speak(tts, sentence)
    speaking.clear()


def speak_async(text):
    t = threading.Thread(target=_speak_worker, args=(text,), daemon=True)
    t.start()
    return t


def stop_speaking():
    interrupted.set()
    stop_tts(tts)
    for _ in range(30):
        if not speaking.is_set():
            break
        time.sleep(0.1)


# ── mic loop ──────────────────────────────────────────────────────────────────

def _mic_loop():
    """
    On desktop: continuously listens and detects interruptions.
    On Android: listens in 6-second chunks (termux limitation).
    """
    while True:
        was_speaking = speaking.is_set()
        text = listen(recognizer)
        if text:
            if was_speaking and speaking.is_set():
                stop_speaking()
                _speech_q.put((text, True))
            else:
                _speech_q.put((text, False))


# ── Grok ─────────────────────────────────────────────────────────────────────

def ask_grok(user_text):
    system_prompt = build_system_prompt(memory)
    messages = build_message_history(memory, system_prompt)
    messages.append({"role": "user", "content": user_text})
    resp = http.post(
        API_URL,
        headers={"Authorization": "Bearer " + API_KEY, "Content-Type": "application/json"},
        json={"model": MODEL, "messages": messages, "max_tokens": 512},
        timeout=30,
    )
    return resp.json()["choices"][0]["message"]["content"]


# ── main session ──────────────────────────────────────────────────────────────

def run_session():
    print("")
    print("Voice chat started. Say 'Until next time' to end.")
    print("-" * 50)

    # ADMC opens
    opener = ask_grok(
        "The user just accepted your request for a voice chat. "
        "Greet them warmly in 1-2 sentences. They value their time so be direct and natural."
    )
    print("ADMC: " + opener)
    speak_async(opener)

    # Start mic in background
    mic_thread = threading.Thread(target=_mic_loop, daemon=True)
    mic_thread.start()

    while True:
        # Get user speech
        try:
            user_text, was_interruption = _speech_q.get(timeout=60)
        except queue.Empty:
            continue
        except (EOFError, KeyboardInterrupt):
            user_text, was_interruption = "until next time", False

        if not user_text:
            continue

        print("You" + (" (interrupted)" if was_interruption else "") + ": " + user_text)

        # Kill switch
        if any(phrase in user_text.lower() for phrase in KILL_PHRASES):
            stop_speaking()
            farewell = "Until next time. Take care."
            print("ADMC: " + farewell)
            speak_async(farewell)
            time.sleep(3)
            add_to_short_term(memory, user_text, farewell)
            save_memory(memory)
            print("Session ended. Memory saved.")
            break

        # After interruption: stop ADMC, wait 2 seconds for user to finish
        if was_interruption:
            stop_speaking()
            print("(Waiting 2 seconds...)")
            time.sleep(2)
            # Grab any extra speech during pause
            while not _speech_q.empty():
                extra, _ = _speech_q.get_nowait()
                user_text = user_text + " " + extra

        # Get response
        try:
            reply = ask_grok(user_text)
        except Exception as e:
            print("ADMC: (Error: " + str(e) + ")")
            continue

        auto_extract_facts(API_KEY, memory, user_text, reply)
        add_to_short_term(memory, user_text, reply)
        auto_summarize_to_long_term(API_KEY, memory)
        save_memory(memory)

        print("ADMC: " + reply)
        speak_async(reply)


# ── entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--accept" in sys.argv or "-a" in sys.argv:
        run_session()
    else:
        send_notification()
        if wait_for_accept():
            run_session()
