"""
CLI chat interface for ADMC Agent.
Run directly: python -m admc_agent.interfaces.cli
"""
from __future__ import annotations

import sys


def run_cli(agent: "ADMCAgent | None" = None) -> None:  # noqa: F821
    """Start an interactive CLI chat session."""
    if agent is None:
        from admc_agent.core.agent import ADMCAgent
        agent = ADMCAgent()
        agent.start()

    user_id = "cli_user"
    print(f"\n{'='*60}")
    print(f"  Welcome to ADMC — Emergent Conscious AI Companion")
    print(f"  Agent: {agent.name}")
    print(f"  Type 'exit' or 'quit' to end the session.")
    print(f"  Type 'goals' to see active goals.")
    print(f"  Type 'emotion' to see current emotional state.")
    print(f"  Type 'reflect' to trigger an inner monologue reflection.")
    print(f"{'='*60}\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[Session ended]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("ADMC: Goodbye. It's been a pleasure. 🌟")
            break

        # Built-in CLI commands
        if user_input.lower() == "goals":
            goals = agent.goal_manager.get_active_goals()
            if goals:
                print("ADMC: My current goals:")
                for g in goals:
                    print(f"  [{g['id']}] {g['description']} (priority {g['priority']})")
            else:
                print("ADMC: I don't have any active goals set right now.")
            continue

        if user_input.lower() == "emotion":
            state = agent.emotions.current_state()
            intensity = agent.emotions.current_intensity()
            print(f"ADMC: I'm feeling {state} with intensity {intensity:.2f}.")
            continue

        if user_input.lower() == "reflect":
            reflection = agent.monologue.reflect()
            print(f"ADMC (inner):\n{reflection}")
            continue

        if user_input.lower().startswith("add goal "):
            desc = user_input[9:].strip()
            goal = agent.goal_manager.add_goal(desc)
            print(f"ADMC: Goal added — [{goal.id}] '{desc}'")
            continue

        # Normal conversation
        response = agent.process_input(user_id, user_input)
        print(f"ADMC: {response}\n")

    agent.stop()


if __name__ == "__main__":
    run_cli()
