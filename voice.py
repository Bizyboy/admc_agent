import os
import sys
import time
import subprocess
import tempfile

# Voice input:  termux-microphone-record (Android native) OR PocketSphinx
# Voice output: pyttsx3 (offline) OR termux-tts-speak (Android native)

TERMUX = os.path.exists("/data/data/com.termux")


# ── TTS ───────────────────────────────────────────────────────────────────────

def init_tts():
    """Return a TTS object or None."""
    if TERMUX:
        # Use termux-tts-speak - always works on Android, no install needed
        return "termux"
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.setProperty("volume", 1.0)
        return engine
    except Exception:
        print("pyttsx3 not available. Install: pip install pyttsx3")
        return None


def speak(tts, text):
    """Speak text. Stops cleanly. Works offline."""
    if tts is None:
        return
    clean = text.replace("*","").replace("#","").replace("`","").replace("_","")
    if tts == "termux":
        try:
            subprocess.run(["termux-tts-speak", clean], timeout=60)
        except Exception as e:
            print("(TTS error: " + str(e) + ")")
    else:
        try:
            tts.say(clean)
            tts.runAndWait()
        except Exception as e:
            print("(TTS error: " + str(e) + ")")


def stop_tts(tts):
    """Stop TTS mid-sentence."""
    if tts == "termux":
        subprocess.run(["pkill", "-f", "termux-tts-speak"], capture_output=True)
    elif tts is not None:
        try:
            tts.stop()
        except Exception:
            pass


# ── Speech Recognition ────────────────────────────────────────────────────────

def init_recognizer():
    """Return recognizer or None."""
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        r.energy_threshold = 300
        r.dynamic_energy_threshold = True
        return r
    except ImportError:
        print("SpeechRecognition not available. Install: pip install SpeechRecognition")
        return None


def _record_termux(seconds=6):
    """Record audio on Android using termux-microphone-record. Returns wav path or None."""
    wav = tempfile.mktemp(suffix=".wav")
    try:
        # Start recording
        subprocess.Popen(["termux-microphone-record", "-f", wav, "-l", str(seconds)])
        time.sleep(seconds)
        # Stop recording
        subprocess.run(["termux-microphone-record", "-q"], capture_output=True)
        time.sleep(0.5)
        if os.path.exists(wav) and os.path.getsize(wav) > 1000:
            return wav
    except Exception as e:
        print("(Record error: " + str(e) + ")")
    return None


def listen(recognizer):
    """
    Listen for speech and return text.
    On Android uses termux-microphone-record.
    On desktop uses the mic directly via pyaudio.
    """
    if TERMUX:
        return _listen_termux(recognizer)
    else:
        return _listen_desktop(recognizer)


def _listen_termux(recognizer):
    """Android: record via termux-microphone-record then transcribe offline."""
    print("Listening... (6 seconds)")
    wav = _record_termux(seconds=6)
    if wav is None:
        print("(Recording failed)")
        return None
    try:
        import speech_recognition as sr
        with sr.AudioFile(wav) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_sphinx(audio)
        except Exception:
            # sphinx fallback - try google if online
            try:
                text = recognizer.recognize_google(audio)
            except Exception:
                text = None
        return text
    except Exception as e:
        print("(Transcribe error: " + str(e) + ")")
        return None
    finally:
        try:
            os.remove(wav)
        except Exception:
            pass


def _listen_desktop(recognizer):
    """Desktop: use mic directly."""
    try:
        import speech_recognition as sr
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)
        print("Processing...")
        try:
            return recognizer.recognize_sphinx(audio)
        except Exception:
            return recognizer.recognize_google(audio)
    except Exception as e:
        err = str(e)
        if "timeout" in err.lower():
            print("(No speech detected)")
        else:
            print("(Could not understand: " + err + ")")
        return None
