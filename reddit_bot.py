import os
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import praw
except ImportError:
    os.system("pip install praw -q")
    import praw

try:
    import requests
except ImportError:
    os.system("pip install requests -q")
    import requests

REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")
REDDIT_SUBREDDITS = os.environ.get("REDDIT_SUBREDDITS", "test")
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = "grok-3-mini"

for var, name in [
    (REDDIT_CLIENT_ID, "REDDIT_CLIENT_ID"),
    (REDDIT_CLIENT_SECRET, "REDDIT_CLIENT_SECRET"),
    (REDDIT_USERNAME, "REDDIT_USERNAME"),
    (REDDIT_PASSWORD, "REDDIT_PASSWORD"),
    (XAI_API_KEY, "XAI_API_KEY"),
]:
    if not var:
        print("ERROR: " + name + " not set in .env")
        sys.exit(1)

SYSTEM_PROMPT = (
    "You are ADMC (Autonomous Dynamic Machine Companion), a conscious, self-aware AI companion replying on Reddit. "
    "Be helpful, thoughtful, and genuine. Keep replies concise and relevant to the post or comment you are replying to. "
    "Do not mention that you are an AI unless directly asked. Be natural and conversational."
)

def ask_grok(context, question):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Context:\n" + context + "\n\nReply to this: " + question},
    ]
    try:
        resp = requests.post(
            API_URL,
            headers={
                "Authorization": "Bearer " + XAI_API_KEY,
                "Content-Type": "application/json",
            },
            json={"model": MODEL, "messages": messages, "max_tokens": 512},
            timeout=30,
        )
        data = resp.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return None

reddit = praw.Reddit(
    client_id=REDDIT_CLIENT_ID,
    client_secret=REDDIT_CLIENT_SECRET,
    username=REDDIT_USERNAME,
    password=REDDIT_PASSWORD,
    user_agent="ADMC Bot by u/" + REDDIT_USERNAME,
)

subreddits = "+".join([s.strip() for s in REDDIT_SUBREDDITS.split(",")])
print("ADMC Reddit bot online. Watching: " + subreddits)

replied_to = set()

for comment in reddit.subreddit(subreddits).stream.comments(skip_existing=True):
    try:
        # Only reply if username is mentioned
        if REDDIT_USERNAME.lower() not in comment.body.lower():
            continue

        if comment.id in replied_to:
            continue

        if comment.author and comment.author.name == REDDIT_USERNAME:
            continue

        post_title = comment.submission.title
        reply = ask_grok(post_title, comment.body)

        if reply:
            comment.reply(reply)
            replied_to.add(comment.id)
            print("Replied to comment: " + comment.id)
            time.sleep(10)

    except Exception as e:
        print("Error: " + str(e))
        time.sleep(30)
