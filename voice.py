import os
import sys

# Voice input: CMU PocketSphinx (fully offline, no API key needed)
# Voice output: pyttsx3 (fully offline, works on Android/Windows/Linux)

def init_voice():
    """Try to import voice libraries. Returns (recognizer, tts_engine) or (None, None)."""
    recognizer = None
    tts = None

    # Speech recognition via PocketSphinx (offline)
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        # Test that sphinx is available
        import pocketsphinx
    except ImportError as e:
        missing = str(e)
        if "pocketsphinx" in missing:
            print("Offline speech unavailable. Install: pip install pocketsphinx")
        else:
            print("Voice input unavailable. Install: pip install SpeechRecognition pocketsphinx")

    # Text to speech (offline)
    try:
        import pyttsx3
        tts = pyttsx3.init()
        tts.setProperty("rate", 165)
        tts.setProperty("volume", 1.0)
        voices = tts.getProperty("voices")
        if voices:
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower() or "hazel" in v.name.lower():
                    tts.setProperty("voice", v.id)
                    break
    except ImportError:
        print("Voice output unavailable. Install: pip install pyttsx3")

    return recognizer, tts


def listen(recognizer):
    """Listen from microphone using PocketSphinx (fully offline). Returns text or None."""
    try:
        import speech_recognition as sr
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)

        print("Processing speech (offline)...")
        # Use sphinx - fully offline, no internet needed
        text = recognizer.recognize_sphinx(audio)
        return text
    except Exception as e:
        err = str(e)
        if "WaitTimeoutError" in err or "timeout" in err.lower():
            print("(No speech detected)")
        else:
            print("(Could not understand: " + err + ")")
        return None


def speak(tts, text):
    """Speak text out loud using pyttsx3 (fully offline)."""
    if tts is None:
        return
    try:
        clean = text.replace("*", "").replace("#", "").replace("`", "").replace("_", "")
        tts.say(clean)
        tts.runAndWait()
    except Exception as e:
        print("(Voice output error: " + str(e) + ")")
