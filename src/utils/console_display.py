"""Rich Console Visualizer for the Agentic Pipeline."""

from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from src.schemas import RubricCheckResult, EvaluationReport, LessonDraft, RejectionLogEntry

console = Console()


class ConsoleDisplay:
    """Rich visualization helper for terminal and Loom video recording."""

    @staticmethod
    def print_header(title: str, subtitle: Optional[str] = None):
        text = Text(title, style="bold cyan")
        if subtitle:
            text.append(f"\n{subtitle}", style="dim")
        console.print(Panel(text, border_style="blue", expand=False))

    @staticmethod
    def print_stage(stage_name: str, description: str):
        console.print(f"\n[bold yellow]▶ STAGE: {stage_name}[/bold yellow] - [dim]{description}[/dim]")

    @staticmethod
    def print_evaluation_report(report: EvaluationReport, iteration: int):
        status_color = "green" if report.overall_passed else "red"
        status_text = "PASSED ALL CHECKPOINTS (READY TO SHIP)" if report.overall_passed else "REJECTED (FAILURES DETECTED)"

        table = Table(
            title=f"Evaluation Rubric Results (Draft Iteration {iteration})",
            title_style="bold magenta",
            border_style=status_color
        )
        table.add_column("Checkpoint Dimension", style="bold white", width=26)
        table.add_column("Verdict", justify="center", width=10)
        table.add_column("Evaluator Rationale & Offending Details", style="dim", width=48)

        for check in report.checks:
            verdict = "[bold green]PASS ✓[/bold green]" if check.passed else "[bold red]FAIL ✗[/bold red]"
            details = check.reasoning
            if not check.passed:
                if check.offending_snippet:
                    details += f"\n[bold yellow]Snippet:[/bold yellow] \"{check.offending_snippet}\""
                if check.prescriptive_action:
                    details += f"\n[bold cyan]Fix:[/bold cyan] {check.prescriptive_action}"
            table.add_row(check.checkpoint.value, verdict, details)

        console.print(table)
        console.print(
            Panel(
                f"[bold {status_color}]Overall System Verdict: {status_text}[/bold {status_color}]",
                border_style=status_color
            )
        )

    @staticmethod
    def print_rejection_log_entry(entry: RejectionLogEntry):
        text = Text()
        text.append(f"Iteration #{entry.iteration} Rejected\n", style="bold red")
        text.append(f"Failed Checkpoints: {', '.join(entry.failed_checks)}\n", style="yellow")
        text.append("Reasons for Rejection:\n", style="bold white")
        for reason in entry.why_it_failed:
            text.append(f"  • {reason}\n", style="dim")
        text.append(f"\nPrescribed Action for Next Iteration:\n  ➔ {entry.what_was_changed_on_retry}", style="cyan")

        console.print(Panel(text, title=f"Rejection Log Entry (Cycle {entry.iteration})", border_style="red"))

    @staticmethod
    def print_lesson_preview(draft: LessonDraft):
        console.print(Panel(
            Markdown(draft.full_content_markdown),
            title=f"[bold green]Generated Lesson (Draft v{draft.iteration}): {draft.title}[/bold green]",
            border_style="green"
        ))

    @staticmethod
    def print_evolution_notice(rules: List[str]):
        if not rules:
            return
        text = Text("Self-Evolving Memory Active - Sharpening Prompts with Learned Rules:\n", style="bold magenta")
        for rule in rules:
            text.append(f"  ⚡ {rule}\n", style="italic")
        console.print(Panel(text, border_style="magenta"))

