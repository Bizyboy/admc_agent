#!/usr/bin/env python3
"""
ADMC Agent — Entry Point

Usage:
  python main.py            # Start interactive CLI chat
  python main.py --chat     # Start interactive CLI chat (explicit)
  python main.py --think    # Start CLI with inner-thought mode enabled
  python main.py --api      # Start FastAPI REST server
  python main.py --daemon   # Run in background daemon mode (no CLI)
"""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ADMC — Emergent Conscious AI Companion"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start the FastAPI REST server instead of the CLI.",
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run agent in background daemon mode (no interactive interface).",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start interactive CLI chat (default mode).",
    )
    parser.add_argument(
        "--think", "--verbose",
        action="store_true",
        dest="think",
        help="Enable inner-thought (verbose) mode — shows the agent's reasoning process.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to config.yaml (default: ./config.yaml).",
    )
    args = parser.parse_args()

    from admc_agent.core.config import get_config
    config = get_config(args.config)

    if args.api:
        try:
            import uvicorn
            from admc_agent.interfaces.api import app
            if app is None:
                print("FastAPI is not installed. Run: pip install fastapi uvicorn")
                sys.exit(1)
            host = config.get("api", "host") or "0.0.0.0"
            port = int(config.get("api", "port") or 8000)
            print(f"Starting ADMC REST API on http://{host}:{port}")
            uvicorn.run(app, host=host, port=port)
        except ImportError:
            print("uvicorn is not installed. Run: pip install uvicorn")
            sys.exit(1)

    elif args.daemon:
        import time
        from admc_agent.core.agent import ADMCAgent
        agent = ADMCAgent(config)
        agent.start()
        print(f"ADMC daemon running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            agent.stop()

    else:
        # Default: interactive CLI chat
        from admc_agent.core.agent import ADMCAgent
        from admc_agent.interfaces.cli import run_cli
        agent = ADMCAgent(config)
        agent.start()
        run_cli(agent, verbose=args.think)


if __name__ == "__main__":
    main()
