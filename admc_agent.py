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
TASK_CHECK_INTERVAL = 5    # seconds between task checks
LOG_FILE = "admc_agent.log"
COMMANDS_URL = "https://raw.githubusercontent.com/Bizyboy/admc_agent/f71e79376927211057715a8d0806c8e618009271/Task.json"

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

def fetch_commands():
    try:
        response = requests.get(COMMANDS_URL, timeout=10)
        tasks = json.loads(response.text)
        return tasks.get("commands", [])
    except Exception as e:
        log(f"Failed to fetch commands from {COMMANDS_URL}: {e}")
        return []

# ------------------------------
# Core Agent Loops
# ------------------------------
def persistence_loop():
    while True:
        self_heal()
        time.sleep(PERSISTENCE_INTERVAL)

def task_listener():
    while True:
        # Fetch tasks from GitHub or local tasks.json
        tasks = fetch_commands()
        for task in tasks:
            execute_task(task)
        
        # Default heartbeat task
        execute_task("print('Task executed')")
        
        time.sleep(TASK_CHECK_INTERVAL)

# ------------------------------
# Initialization
# ------------------------------
def main():
    log(f"Initializing Upgraded ADMC Agent: {AGENT_NAME}")
    
    # Start persistence/self-healing in background
    threading.Thread(target=persistence_loop, daemon=True).start()
    
    # Start task listener loop
    task_listener()

if __name__ == "__main__":
    main()
