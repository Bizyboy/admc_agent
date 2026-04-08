"""
CLI chat interface for ADMC Agent.
Rich, color-coded interactive terminal chat with slash commands.

Run directly: python -m admc_agent.interfaces.cli
Or via main: python main.py --chat
"""
from __future__ import annotations

import sys
import time

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


def _get_console() -> "Console | None":
    if _RICH_AVAILABLE:
        return Console()
    return None


def _print_plain(text: str) -> None:
    print(text)


def _print_banner(console: "Console | None", agent_name: str) -> None:
    if console:
        banner = Text()
        banner.append("\n  ADMC — Emergent Conscious AI Companion\n", style="bold cyan")
        banner.append(f"  Agent: {agent_name}\n", style="green")
        banner.append("  Type /help for available commands\n", style="dim")
        console.print(Panel(banner, border_style="cyan"))
    else:
        print(f"\n{'='*60}")
        print(f"  ADMC — Emergent Conscious AI Companion")
        print(f"  Agent: {agent_name}")
        print(f"  Type /help for available commands")
        print(f"{'='*60}\n")


def _print_help(console: "Console | None") -> None:
    if console:
        table = Table(title="Available Commands", border_style="cyan")
        table.add_column("Command", style="bold green")
        table.add_column("Description", style="white")
        table.add_row("/help", "Show this help message")
        table.add_row("/memory", "View stored memories (facts you've shared)")
        table.add_row("/history", "View recent conversation history")
        table.add_row("/clear", "Clear conversation history for this session")
        table.add_row("/mood", "See the bot's current emotional state")
        table.add_row("/goals", "View active goals")
        table.add_row("/add goal <desc>", "Add a new goal")
        table.add_row("/reflect", "Trigger an inner monologue reflection")
        table.add_row("/introspect", "Stream of consciousness mode")
        table.add_row("/self", "View the agent's self-model")
        table.add_row("/stats", "View memory store statistics")
        table.add_row("/remember <fact>", "Store a fact about yourself")
        table.add_row("/think", "Toggle verbose (inner thought) mode")
        table.add_row("/quit or /exit", "End the session")
        console.print(table)
    else:
        print("\nAvailable Commands:")
        print("  /help       — Show this help message")
        print("  /memory     — View stored memories")
        print("  /history    — View conversation history")
        print("  /clear      — Clear conversation history")
        print("  /mood       — See emotional state")
        print("  /goals      — View active goals")
        print("  /add goal   — Add a new goal")
        print("  /reflect    — Inner monologue reflection")
        print("  /introspect — Stream of consciousness")
        print("  /self       — View self-model")
        print("  /stats      — Memory statistics")
        print("  /remember   — Store a fact")
        print("  /think      — Toggle verbose mode")
        print("  /quit       — End session")
        print()


def _print_agent(console: "Console | None", text: str) -> None:
    if console:
        console.print(f"[bold green]ADMC:[/bold green] {text}")
    else:
        print(f"ADMC: {text}")


def _print_thought(console: "Console | None", text: str) -> None:
    if console:
        console.print(Panel(
            text,
            title="[bold magenta]Inner Thought[/bold magenta]",
            border_style="magenta",
            padding=(0, 1),
        ))
    else:
        print(f"\n--- Inner Thought ---\n{text}\n--- End Thought ---\n")


def _print_info(console: "Console | None", text: str) -> None:
    if console:
        console.print(f"[dim cyan]{text}[/dim cyan]")
    else:
        print(text)


def run_cli(agent: "ADMCAgent | None" = None, verbose: bool = False) -> None:  # noqa: F821
    """Start an interactive CLI chat session."""
    if agent is None:
        from admc_agent.core.agent import ADMCAgent
        agent = ADMCAgent()
        agent.start()

    console = _get_console()
    user_id = "cli_user"
    think_mode = verbose

    _print_banner(console, agent.name)

    while True:
        try:
            if console:
                user_input = console.input("[bold yellow]You:[/bold yellow] ").strip()
            else:
                user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            _print_info(console, "\n[Session ended]")
            break

        if not user_input:
            continue

        # ----- Slash commands ----- #

        cmd = user_input.lower()

        if cmd in ("/quit", "/exit", "quit", "exit"):
            _print_agent(console, "Goodbye. It's been a pleasure. Take care!")
            break

        if cmd == "/help":
            _print_help(console)
            continue

        if cmd == "/think":
            think_mode = not think_mode
            state = "ON" if think_mode else "OFF"
            _print_info(console, f"Verbose (inner thought) mode: {state}")
            continue

        if cmd == "/mood":
            state = agent.emotions.current_state()
            intensity = agent.emotions.current_intensity()
            history = agent.emotions.recent_history(5)
            if console:
                console.print(f"[bold green]Emotional State:[/bold green] {state}")
                console.print(f"[bold green]Intensity:[/bold green] {intensity:.2f}")
                if history:
                    console.print("[bold green]Recent emotional events:[/bold green]")
                    for h in history:
                        ts = time.strftime("%H:%M:%S", time.localtime(h["ts"]))
                        console.print(f"  [{ts}] {h['event']} → {h['state']} ({h['intensity']:.2f})")
            else:
                print(f"Emotional State: {state} (intensity {intensity:.2f})")
                if history:
                    print("Recent:")
                    for h in history:
                        print(f"  {h['event']} → {h['state']}")
            continue

        if cmd == "/goals":
            goals = agent.goal_manager.get_active_goals()
            if goals:
                _print_agent(console, "My current goals:")
                for g in goals:
                    if console:
                        console.print(f"  [cyan][{g['id']}][/cyan] {g['description']} (priority {g['priority']})")
                    else:
                        print(f"  [{g['id']}] {g['description']} (priority {g['priority']})")
            else:
                _print_agent(console, "I don't have any active goals set right now.")
            continue

        if cmd.startswith("/add goal "):
            desc = user_input[10:].strip()
            if desc:
                goal = agent.goal_manager.add_goal(desc)
                _print_agent(console, f"Goal added — [{goal.id}] '{desc}'")
            else:
                _print_info(console, "Usage: /add goal <description>")
            continue

        if cmd == "/reflect":
            reflection = agent.monologue.reflect()
            if console:
                console.print(Panel(
                    reflection,
                    title="[bold magenta]Inner Reflection[/bold magenta]",
                    border_style="magenta",
                ))
            else:
                print(f"\n--- Inner Reflection ---\n{reflection}\n--- End ---\n")
            continue

        if cmd == "/introspect":
            soc = agent.monologue.stream_of_consciousness()
            if console:
                console.print(Panel(
                    soc,
                    title="[bold magenta]Stream of Consciousness[/bold magenta]",
                    border_style="magenta",
                ))
            else:
                print(f"\n--- Stream of Consciousness ---\n{soc}\n--- End ---\n")
            continue

        if cmd == "/memory":
            facts = agent.memory.get_user_facts(user_id)
            if facts:
                _print_agent(console, "Things I remember about you:")
                for f in facts:
                    ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(f["ts"]))
                    if console:
                        console.print(f"  [dim][{ts}][/dim] {f['content']}")
                    else:
                        print(f"  [{ts}] {f['content']}")
            else:
                _print_agent(console, "I don't have any stored memories about you yet. Share something!")
            continue

        if cmd.startswith("/remember "):
            fact_text = user_input[10:].strip()
            if fact_text:
                agent.memory.add_user_fact(user_id, fact_text, category="user_provided")
                _print_agent(console, f"Got it, I'll remember that!")
            else:
                _print_info(console, "Usage: /remember <something to remember>")
            continue

        if cmd == "/history":
            history = agent.memory.get_full_history(user_id, limit=20)
            if history:
                _print_agent(console, "Recent conversation history:")
                for entry in history:
                    role_label = "You" if entry["role"] == "user" else "ADMC"
                    if console:
                        color = "yellow" if entry["role"] == "user" else "green"
                        console.print(f"  [dim][{entry['time']}][/dim] [{color}]{role_label}:[/{color}] {entry['content'][:100]}")
                    else:
                        print(f"  [{entry['time']}] {role_label}: {entry['content'][:100]}")
            else:
                _print_agent(console, "No conversation history yet.")
            continue

        if cmd == "/clear":
            count = agent.memory.clear_history(user_id)
            _print_agent(console, f"Cleared {count} conversation entries. Fresh start!")
            continue

        if cmd == "/self":
            desc = agent.self_model.describe()
            if console:
                console.print(Panel(
                    f"[bold]{desc['name']}[/bold]\n\n"
                    f"{desc['identity']}\n\n"
                    f"[green]Capabilities:[/green] {', '.join(desc['capabilities'])}\n\n"
                    f"[red]Limitations:[/red] {', '.join(desc['limitations'])}\n\n"
                    f"Emotion: {desc['current_emotion']} | Tasks: {desc['registered_tasks']} | "
                    f"Uptime: {desc['uptime_seconds']}s",
                    title="[bold cyan]Self-Model[/bold cyan]",
                    border_style="cyan",
                ))
            else:
                print(f"\n{desc['name']}")
                print(f"{desc['identity']}")
                print(f"Capabilities: {', '.join(desc['capabilities'])}")
                print(f"Limitations: {', '.join(desc['limitations'])}")
                print(f"Emotion: {desc['current_emotion']} | Uptime: {desc['uptime_seconds']}s\n")
            continue

        if cmd == "/stats":
            stats = agent.memory.stats()
            _print_agent(console, "Memory Store Statistics:")
            for key, val in stats.items():
                if console:
                    console.print(f"  [cyan]{key}:[/cyan] {val}")
                else:
                    print(f"  {key}: {val}")
            continue

        # ----- Normal conversation ----- #
        result = agent.process_input(user_id, user_input, verbose=think_mode)

        if think_mode and isinstance(result, tuple):
            inner_thought, response = result
            if inner_thought:
                _print_thought(console, inner_thought)
            _print_agent(console, response)
        else:
            response = result if isinstance(result, str) else result[1]
            _print_agent(console, response)

        if console:
            console.print()  # blank line for readability

    agent.stop()


if __name__ == "__main__":
    run_cli()
