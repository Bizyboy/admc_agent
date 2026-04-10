import os
import sys
import tempfile

# Voice input via SpeechRecognition
# Voice output via pyttsx3 (offline, works on Android/Windows/Linux)

def init_voice():
    """Try to import voice libraries. Returns (recognizer, tts_engine) or (None, None)."""
    recognizer = None
    tts = None

    # Speech recognition
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
    except ImportError:
        print("Voice input unavailable. Install: pip install SpeechRecognition")

    # Text to speech
    try:
        import pyttsx3
        tts = pyttsx3.init()
        tts.setProperty("rate", 165)
        tts.setProperty("volume", 1.0)
        # Try to set a natural voice if available
        voices = tts.getProperty("voices")
        if voices:
            # Prefer a female voice if available
            for v in voices:
                if "female" in v.name.lower() or "zira" in v.name.lower() or "hazel" in v.name.lower():
                    tts.setProperty("voice", v.id)
                    break
    except ImportError:
        print("Voice output unavailable. Install: pip install pyttsx3")

    return recognizer, tts


def listen(recognizer):
    """Listen from microphone and return text. Returns None on failure."""
    try:
        import speech_recognition as sr
        with sr.Microphone() as source:
            print("Listening... (speak now)")
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)

        print("Processing speech...")
        text = recognizer.recognize_google(audio)
        return text
    except Exception as e:
        err = str(e)
        if "WaitTimeoutError" in err or "timeout" in err.lower():
            print("(No speech detected)")
        else:
            print("(Could not understand: " + err + ")")
        return None


def speak(tts, text):
    """Speak text out loud."""
    if tts is None:
        return
    try:
        # Clean up text for speech (remove markdown symbols)
        clean = text.replace("*", "").replace("#", "").replace("`", "").replace("_", "")
        tts.say(clean)
        tts.runAndWait()
    except Exception as e:
        print("(Voice output error: " + str(e) + ")")
