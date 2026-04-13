"""
ADMC Continuous Voice Chat
--------------------------
ADMC sends you a desktop notification requesting a chat.
Accept it and a continuous two-way voice conversation begins.
Say or type "Until next time" to end the session.
Interrupt ADMC while he speaks and he stops immediately,
waits 2 seconds for you to finish, then responds.

Run:
    python voice_chat.py            # ADMC requests a chat now
    python voice_chat.py --accept   # Skip notification, start immediately
"""

import os
import sys
import time
import threading
import queue

# ── env ──────────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import requests as http

API_KEY = os.environ.get("XAI_API_KEY", "")
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL   = "grok-3-mini"

if not API_KEY:
    print("ERROR: XAI_API_KEY not set in .env")
    sys.exit(1)

# ── memory ───────────────────────────────────────────────────────────────────
from memory import (
    load_memory, save_memory, build_system_prompt,
    build_message_history, add_to_short_term,
    auto_extract_facts, auto_summarize_to_long_term,
)

memory = load_memory()

# ── optional imports ─────────────────────────────────────────────────────────
try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    _tts_engine.setProperty("rate", 160)
    _tts_engine.setProperty("volume", 1.0)
    TTS_OK = True
except Exception:
    TTS_OK = False
    print("pyttsx3 not available — install: pip install pyttsx3")

try:
    import speech_recognition as sr
    _recognizer = sr.Recognizer()
    _recognizer.energy_threshold = 300
    _recognizer.dynamic_energy_threshold = True
    MIC_OK = True
except Exception:
    MIC_OK = False
    print("SpeechRecognition not available — install: pip install SpeechRecognition pyaudio")

try:
    from plyer import notification as _plyer_notif
    PLYER_OK = True
except Exception:
    PLYER_OK = False

KILL_PHRASES = {"until next time", "goodbye admc", "end session", "stop chat"}

# ── state shared across threads ───────────────────────────────────────────────
interrupted   = threading.Event()   # set when user interrupts
speaking      = threading.Event()   # set while TTS is active
response_q    = queue.Queue()       # grok replies land here


# ── notification ──────────────────────────────────────────────────────────────
def send_notification():
    """
    Send a desktop/system notification asking the user to start a voice chat.
    Falls back gracefully on Android / headless environments.
    """
    title   = "ADMC is requesting a chat"
    message = "Your companion wants to talk. Run python voice_chat.py --accept to connect."

    # Try plyer (Windows / Linux / macOS)
    if PLYER_OK:
        try:
            _plyer_notif.notify(
                title=title,
                message=message,
                app_name="ADMC",
                timeout=15,
            )
            print("[ADMC] Desktop notification sent.")
            return
        except Exception:
            pass

    # Termux notify-send (Android)
    if os.path.exists("/data/data/com.termux"):
        os.system("termux-notification --title 'ADMC' --content '" + message + "' --id 42 &")
        print("[ADMC] Termux notification sent.")
        return

    # Fallback — terminal bell + print
    print("\a")
    print("=" * 55)
    print("  ADMC is requesting a voice chat.")
    print("  Press ENTER to accept or Ctrl+C to decline.")
    print("=" * 55)


def wait_for_accept():
    """Block until the user accepts (presses Enter) or Ctrl+C."""
    try:
        input("Press ENTER to start voice chat with ADMC...\n")
        return True
    except (EOFError, KeyboardInterrupt):
        print("Session declined.")
        return False


# ── TTS with interruption ─────────────────────────────────────────────────────
def _speak_worker(text):
    """Run in a thread. Stops if interrupted event is set."""
    if not TTS_OK:
        print("ADMC: " + text)
        return

    # Split into sentences so we can stop between them
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    speaking.set()
    interrupted.clear()

    for sentence in sentences:
        if interrupted.is_set():
            break
        try:
            _tts_engine.say(sentence)
            _tts_engine.runAndWait()
        except Exception:
            break

    speaking.clear()


def speak_async(text):
    """Speak text in a background thread, interruptible."""
    t = threading.Thread(target=_speak_worker, args=(text,), daemon=True)
    t.start()
    return t


def stop_speaking():
    """Signal the TTS thread to stop and wait for it to clear."""
    interrupted.set()
    try:
        _tts_engine.stop()
    except Exception:
        pass
    # Wait until speaking clears
    for _ in range(20):
        if not speaking.is_set():
            break
        time.sleep(0.1)


# ── microphone listener ───────────────────────────────────────────────────────
def listen_once(timeout=8, phrase_limit=20):
    """
    Listen for one utterance.
    Returns (text, was_interrupted) where was_interrupted=True means
    the user spoke while ADMC was talking.
    """
    if not MIC_OK:
        # Fallback to keyboard
        try:
            text = input("You: ").strip()
            return text, False
        except (EOFError, KeyboardInterrupt):
            return "until next time", False

    was_speaking = speaking.is_set()

    try:
        with sr.Microphone() as source:
            _recognizer.adjust_for_ambient_noise(source, duration=0.3)
            audio = _recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
    except sr.WaitTimeoutError:
        return None, False
    except Exception as e:
        return None, False

    try:
        text = _recognizer.recognize_google(audio)
        return text, was_speaking
    except Exception:
        return None, False


# ── Grok call ─────────────────────────────────────────────────────────────────
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


# ── background listener thread ────────────────────────────────────────────────
_user_speech_q = queue.Queue()

def _mic_loop():
    """
    Continuously listens in background.
    If user speaks while ADMC is talking → interrupt.
    Otherwise queue the speech for the main loop.
    """
    while True:
        text, was_interruption = listen_once(timeout=10, phrase_limit=20)
        if text is None:
            continue
        if was_interruption and speaking.is_set():
            stop_speaking()
        _user_speech_q.put((text, was_interruption))


# ── main session ──────────────────────────────────────────────────────────────
def run_voice_session():
    print("")
    print("Voice chat started. Say 'Until next time' to end.")
    print("-" * 50)

    # ADMC opens the conversation
    opener = ask_grok(
        "The user just accepted your request for a voice chat. "
        "Greet them warmly and naturally in 1-2 sentences. "
        "Remember: they are busy and value their time, so be direct."
    )
    print("ADMC: " + opener)
    speak_async(opener)

    # Start background mic loop
    if MIC_OK:
        mic_thread = threading.Thread(target=_mic_loop, daemon=True)
        mic_thread.start()

    while True:
        # Wait for user speech
        try:
            if MIC_OK:
                user_text, was_interruption = _user_speech_q.get(timeout=30)
            else:
                raw = input("You: ").strip()
                user_text, was_interruption = raw, False
        except queue.Empty:
            # No speech for 30 seconds — check if still alive
            continue
        except (EOFError, KeyboardInterrupt):
            user_text = "until next time"
            was_interruption = False

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
            print("")
            print("Session ended.")
            break

        # If interrupted, stop ADMC and wait 2 seconds for user to finish
        if was_interruption:
            stop_speaking()
            print("(Pausing 2 seconds...)")
            time.sleep(2)

            # Drain any extra speech queued during pause
            while not _user_speech_q.empty():
                extra, _ = _user_speech_q.get_nowait()
                user_text = user_text + " " + extra

        # Get Grok response in background while we wait
        try:
            reply = ask_grok(user_text)
        except Exception as e:
            print("ADMC: (Error: " + str(e) + ")")
            continue

        # Auto memory
        auto_extract_facts(API_KEY, memory, user_text, reply)
        add_to_short_term(memory, user_text, reply)
        auto_summarize_to_long_term(API_KEY, memory)
        save_memory(memory)

        print("ADMC: " + reply)
        speak_async(reply)


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    auto_accept = "--accept" in sys.argv or "-a" in sys.argv

    if auto_accept:
        run_voice_session()
    else:
        send_notification()
        accepted = wait_for_accept()
        if accepted:
            run_voice_session()
