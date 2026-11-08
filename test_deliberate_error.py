#!/usr/bin/env python3
"""Dedicated demonstration script for the Loom video: Evaluator catching a deliberate error."""

import sys
from rich.console import Console
from rich.panel import Panel

from src.utils.llm_client import LLMClient
from src.generator.generator import LessonGenerator
from src.evaluator.evaluator import ContentEvaluator
from src.memory.evolution_manager import EvolutionMemoryManager
from src.graph.workflow import ContentGraphOrchestrator
from src.utils.console_display import ConsoleDisplay

console = Console()


def run_deliberate_error_demo():
    """Runs a 2-stage demonstration:

    1. Draft 1 is injected with deliberate PhD-level jargon.
    2. Evaluator catches it, fails the NO_UNEXPLAINED_JARGON checkpoint with zero partial credit.
    3. Rejection Log records the failure and prescribes the fix.
    4. Generator regenerates Draft 2 removing the jargon and replacing it with an open-book analogy.
    5. Evaluator passes Draft 2 100%.
    """
    ConsoleDisplay.print_header(
        "DEMO: Evaluator Catching a Deliberate Error (Loom Video Demo)",
        "Demonstrating hard pass/fail gates, rejection logging, and self-correction loop"
    )

    console.print(Panel(
        "[bold yellow]SCENARIO:[/bold yellow]\n"
        "We instruct the generator to deliberately violate our beginner rubric by injecting dense PhD-level jargon:\n"
        "[italic]'dense vector embeddings in 1536-dimensional latent space', 'cross-entropy loss', 'cosine similarity metrics'[/italic].\n\n"
        "[bold cyan]EXPECTED AGENTIC BEHAVIOR:[/bold cyan]\n"
        "1. The evaluator MUST catch this violation.\n"
        "2. The evaluator MUST reject the draft with ZERO partial credit.\n"
        "3. The system MUST log the exact offending phrase into the Rejection Log.\n"
        "4. The system MUST feed back actionable corrections and regenerate clean content.",
        title="Test Case Hypothesis",
        border_style="yellow"
    ))

    # Initialize subsystems
    llm_client = LLMClient()
    generator = LessonGenerator(llm_client=llm_client)
    evaluator = ContentEvaluator(llm_client=llm_client)
    memory_manager = EvolutionMemoryManager()

    orchestrator = ContentGraphOrchestrator(
        generator=generator,
        evaluator=evaluator,
        memory_manager=memory_manager
    )

    result_state = orchestrator.run(
        topic="Introduction to RAG",
        max_retries=2,
        deliberate_error_type="PHD_JARGON"
    )

    console.print("\n" + "="*70)
    console.print("[bold green]DEMONSTRATION COMPLETE:[/bold green]")
    console.print(f"Total Iterations: {result_state['iteration']}")
    console.print(f"Final Approval Status: {result_state['is_final_approved']}")
    console.print(f"Rejection Log Entries Count: {len(result_state['rejection_log'])}")
    console.print("="*70 + "\n")


if __name__ == "__main__":
    run_deliberate_error_demo()

