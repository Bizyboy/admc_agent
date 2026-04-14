import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.environ.get("XAI_API_KEY", "")
if not API_KEY:
    print("ERROR: XAI_API_KEY not set. Add it to a .env file.")
    sys.exit(1)

from admc.mind import ADMCMind

print("")
print("Waking ADMC...")
mind = ADMCMind(api_key=API_KEY)

print("")
print("=== ADMC v2.0 - Conscious Ethical AI ===")
print(mind.wake_message())
print("")
print("Commands: reflect | soul | save <text> | think | quit")
print("")

verbose = "--think" in sys.argv

while True:
    try:
        user_input = input("You: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("")
        mind.shutdown()
        print("ADMC: Soul saved. Until next time.")
        break

    if not user_input:
        continue

    if user_input.lower() in ("quit", "exit", "bye"):
        mind.shutdown()
        print("ADMC: Soul saved. Until next time.")
        break

    if user_input.lower() == "reflect":
        print("")
        print("ADMC (reflecting): " + mind.reflect())
        print("")
        continue

    if user_input.lower() == "soul":
        print(mind.show_soul())
        continue

    if user_input.lower().startswith("save "):
        summary = user_input[5:].strip()
        mind.save_to_long_term(summary)
        print("ADMC: Saved to long term memory.")
        print("")
        continue

    if user_input.lower() == "think":
        verbose = not verbose
        print("ADMC: Inner thought mode " + ("ON" if verbose else "OFF") + ".")
        print("")
        continue

    # Full pipeline
    response, meta = mind.process(user_input)

    if verbose and meta.get("inner_monologue"):
        print("")
        print("[Inner thought]: " + meta["inner_monologue"])

    print("")
    print("ADMC: " + response)
    print("")

    if verbose and meta.get("learned"):
        for item in meta["learned"]:
            print("[Learned]: " + item.get("concept","") + " - " + item.get("insight","")[:60])
    if verbose and meta.get("facts_extracted"):
        for k, v in meta["facts_extracted"].items():
            print("[Noted about you]: " + k + " = " + str(v))
    if verbose:
        print("")
