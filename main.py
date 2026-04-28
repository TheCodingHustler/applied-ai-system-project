import sys

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich import box

from agent import Agent

console = Console()
agent = Agent()

ERROR_TYPE_COLORS = {
    "syntax": "red",
    "runtime": "orange3",
    "logic": "yellow",
    "dependency": "cyan",
    "config": "magenta",
    "unknown": "grey50",
}


def render_plan(steps: list, goal: str):
    console.print(
        Panel(f"[bold green]{goal}[/bold green]", title="Plan Created", border_style="green")
    )
    table = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan", expand=True)
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Step", style="bold white", min_width=20)
    table.add_column("Description")
    table.add_column("Est. Time", style="cyan", width=12, justify="right")

    for step in steps:
        table.add_row(
            str(step["id"]),
            step["title"],
            step["description"],
            step["estimated_time"],
        )

    console.print(table)
    console.print(
        f"[dim]Tip: say [bold]done step 1[/bold] when you finish a step, "
        f"or [bold]progress[/bold] to see your status.[/dim]"
    )


def render_debug(diagnosis: dict):
    error_type = diagnosis.get("error_type", "unknown")
    color = ERROR_TYPE_COLORS.get(error_type, "white")
    language = diagnosis.get("language", "text")

    console.print(
        Panel(
            f"[bold {color}]{error_type.upper()} ERROR[/bold {color}]",
            title="Classification",
            border_style=color,
        )
    )
    console.print(
        Panel(diagnosis.get("root_cause", ""), title="[bold]Root Cause[/bold]", border_style="yellow")
    )
    console.print(
        Panel(
            diagnosis.get("fix_explanation", ""),
            title="[bold]How to Fix[/bold]",
            border_style="green",
        )
    )

    fixed_code = diagnosis.get("fixed_code")
    if fixed_code:
        syntax = Syntax(fixed_code, language, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="[bold]Fixed Code[/bold]", border_style="blue"))


def render_explain(text: str):
    console.print(Panel(text, title="[bold cyan]Explanation[/bold cyan]", border_style="cyan"))


def render_progress(progress: dict):
    if not progress["goal"]:
        console.print(
            Panel(
                "[dim]No active plan. Tell me a goal to get started.[/dim]",
                border_style="dim",
            )
        )
        return

    header = (
        f"[bold]{progress['goal']}[/bold]\n\n"
        f"[green]{progress['done']}[/green] / {progress['total']} steps complete  "
        f"[cyan]{progress['percent']}%[/cyan]"
    )
    console.print(Panel(header, title="Current Plan", border_style="blue"))

    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_column("", width=3)
    table.add_column("", width=4, style="dim")
    table.add_column("")

    for step in progress["steps"]:
        if step["done"]:
            status = "[green]✓[/green]"
            title = Text(step["title"], style="dim strike")
        else:
            status = "[dim]○[/dim]"
            title = Text(step["title"])
        table.add_row(status, str(step["id"]), title)

    console.print(table)


def render_track(result: dict):
    action = result.get("action")

    if action == "reset":
        console.print(
            Panel("[yellow]Plan cleared. Ready for a new goal.[/yellow]", border_style="yellow")
        )
        return

    if action in ("mark_done", "mark_undone"):
        step_id = result.get("step_id")
        success = result.get("success")
        verb = "completed" if action == "mark_done" else "reopened"
        if success:
            console.print(f"[green]✓[/green] Step {step_id} marked as {verb}.")
        else:
            console.print(f"[red]✗[/red] Step {step_id} not found in your plan.")

    progress = result.get("progress")
    if progress:
        render_progress(progress)


def render_error(message: str):
    console.print(Panel(f"[red]{message}[/red]", title="Error", border_style="red"))


def render_result(result: dict):
    rtype = result.get("type")
    if rtype == "plan":
        render_plan(result["steps"], result["goal"])
    elif rtype == "debug":
        render_debug(result["diagnosis"])
    elif rtype == "explain":
        render_explain(result["text"])
    elif rtype == "track":
        render_track(result)
    elif rtype == "error":
        render_error(result["message"])


def print_welcome():
    console.print(
        Panel(
            "[bold cyan]AI Task Planner + Debugger[/bold cyan]\n\n"
            "[dim]What you can do:[/dim]\n\n"
            "  [green]Plan a goal[/green]   Build a REST API for user auth\n"
            "  [red]Debug code[/red]    TypeError: cannot read property 'id' of undefined\n"
            "  [cyan]Ask anything[/cyan]  What does step 3 mean? How do I set up JWT?\n"
            "  [blue]Track steps[/blue]   done step 2  |  progress  |  reset\n\n"
            "[dim]Type [bold]exit[/bold] to quit.[/dim]",
            title="Welcome",
            border_style="cyan",
        )
    )


def main():
    print_welcome()

    while True:
        try:
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye.[/dim]")
            sys.exit(0)

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            console.print("[dim]Goodbye.[/dim]")
            sys.exit(0)

        with console.status("[dim]Thinking...[/dim]", spinner="dots"):
            result = agent.run(user_input)

        render_result(result)


if __name__ == "__main__":
    main()
