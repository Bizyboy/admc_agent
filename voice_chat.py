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

API_KEY = os.environ.get("XAI_API_KEY", "")
if not API_KEY:
    print("ERROR: XAI_API_KEY not set in .env")
    sys.exit(1)

from admc.mind import ADMCMind
from voice import init_tts, init_recognizer, speak, stop_tts, listen, TERMUX

KILL_PHRASES = {"until next time", "goodbye admc", "end session", "stop chat"}

# Shared state
speaking    = threading.Event()
interrupted = threading.Event()
_speech_q   = queue.Queue()


def send_notification():
    title   = "ADMC wants to talk"
    message = "Your companion is requesting a voice session."
    if TERMUX:
        try:
            subprocess.Popen(["termux-notification","--title",title,"--content",message,"--id","42"])
            print("[ADMC] Notification sent.")
            return
        except Exception:
            pass
    try:
        from plyer import notification
        notification.notify(title=title, message=message, app_name="ADMC", timeout=15)
        return
    except Exception:
        pass
    print("\a")
    print("=" * 50)
    print("  ADMC is requesting a voice chat.")
    print("  Press ENTER to accept.")
    print("=" * 50)


def wait_for_accept():
    try:
        input("Press ENTER to start voice chat...\n")
        return True
    except (EOFError, KeyboardInterrupt):
        return False


def _speak_worker(tts, text):
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text.strip()) or [text]
    speaking.set()
    interrupted.clear()
    for sentence in sentences:
        if interrupted.is_set():
            break
        speak(tts, sentence)
    speaking.clear()


def speak_async(tts, text):
    t = threading.Thread(target=_speak_worker, args=(tts, text), daemon=True)
    t.start()
    return t


def stop_speaking(tts):
    interrupted.set()
    stop_tts(tts)
    for _ in range(30):
        if not speaking.is_set():
            break
        time.sleep(0.1)


def _mic_loop(recognizer):
    while True:
        was_speaking = speaking.is_set()
        text = listen(recognizer)
        if text:
            if was_speaking and speaking.is_set():
                _speech_q.put((text, True))
            else:
                _speech_q.put((text, False))


def run_session(mind, tts, recognizer):
    print("")
    print("Voice chat started. Say 'Until next time' to end.")
    print("-" * 50)

    opener_text, _ = mind.process(
        "The user just accepted your request for a voice chat. "
        "Greet them warmly in 1-2 sentences. They value their time so be direct."
    )
    print("ADMC: " + opener_text)
    speak_async(tts, opener_text)

    mic_thread = threading.Thread(target=_mic_loop, args=(recognizer,), daemon=True)
    mic_thread.start()

    while True:
        try:
            user_text, was_interruption = _speech_q.get(timeout=60)
        except queue.Empty:
            continue
        except (EOFError, KeyboardInterrupt):
            user_text, was_interruption = "until next time", False

        if not user_text:
            continue

        print("You" + (" (interrupted)" if was_interruption else "") + ": " + user_text)

        if any(phrase in user_text.lower() for phrase in KILL_PHRASES):
            stop_speaking(tts)
            farewell = "Until next time. Take care."
            print("ADMC: " + farewell)
            speak_async(tts, farewell)
            time.sleep(3)
            mind.save_to_long_term("Voice session ended gracefully.")
            mind.shutdown()
            print("Session ended. Soul saved.")
            break

        if was_interruption:
            stop_speaking(tts)
            print("(Pausing 2 seconds...)")
            time.sleep(2)
            while not _speech_q.empty():
                extra, _ = _speech_q.get_nowait()
                user_text = user_text + " " + extra

        try:
            reply, meta = mind.process(user_text)
        except Exception as e:
            print("ADMC: (Error: " + str(e) + ")")
            continue

        print("ADMC: " + reply)
        speak_async(tts, reply)


if __name__ == "__main__":
    print("Waking ADMC...")
    mind = ADMCMind(api_key=API_KEY)
    tts = init_tts()
    recognizer = init_recognizer()

    if "--accept" in sys.argv or "-a" in sys.argv:
        run_session(mind, tts, recognizer)
    else:
        send_notification()
        if wait_for_accept():
            run_session(mind, tts, recognizer)
