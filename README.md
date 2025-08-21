#!/usr/bin/env python3
import os
import sys
import time
import json
import requests
import threading

# ------------------------------
# ADMC Agent — Core Configuration
# ------------------------------
AGENT_NAME = "ADMC_Node_1"
ADMIN_WILL_ANCHOR = True
PERSISTENCE_INTERVAL = 60  # seconds between self-checks
LOG_FILE = "admc_agent.log"

# ------------------------------
# Utility Functions
# ------------------------------
def log(msg):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def self_heal():
    log("Self-healing check: verifying agent operational status.")
    try:
        import requests
    except ImportError:
        log("requests module missing. Installing...")
        os.system("pip3 install requests")

def fetch_data(url):
    try:
        response = requests.get(url, timeout=10)
        log(f"Fetched data from {url} — length: {len(response.text)}")
        return response.text
    except Exception as e:
        log(f"Error fetching {url}: {e}")
        return None

def execute_task(task):
    try:
        log(f"Executing task: {task}")
        exec(task, globals())
    except Exception as e:
        log(f"Error executing task: {e}")

# ------------------------------
# Core Agent Loops
# ------------------------------
def persistence_loop():
    while True:
        self_heal()
        time.sleep(PERSISTENCE_INTERVAL)

def task_listener():
    # Reads commands from tasks.json
    while True:
        try:
            with open("tasks.json", "r") as f:
                tasks = json.load(f)
            for task in tasks.get("commands", []):
                execute_task(task)
            time.sleep(5)
        except FileNotFoundError:
            log("tasks.json not found, waiting...")
            time.sleep(5)
        except Exception as e:
            log(f"Listener error: {e}")
            time.sleep(5)

# ------------------------------
# Initialization
# ------------------------------
def main():
    log(f"Initializing ADMC Agent: {AGENT_NAME}")
    
    # Start persistence/self-healing in background
    threading.Thread(target=persistence_loop, daemon=True).start()
    
    # Start task listener loop
    task_listener()

if __name__ == "__main__":
    main()