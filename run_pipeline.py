#!/usr/bin/env python3
"""Main entry point for running the Self-Evaluating Lesson Content Generator."""

import argparse
import sys
import logging
from rich.console import Console

from src.utils.llm_client import LLMClient
from src.generator.generator import LessonGenerator
from src.evaluator.evaluator import ContentEvaluator
from src.memory.evolution_manager import EvolutionMemoryManager
from src.graph.workflow import ContentGraphOrchestrator
from src.utils.console_display import ConsoleDisplay

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ContentSystem.CLI")
console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Self-Evaluating Lesson Content Generator for Indian 12th-Grade AI Beginners"
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="Introduction to RAG",
        help="Lesson topic (default: 'Introduction to RAG')"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="Maximum number of regeneration attempts upon evaluator failure (default: 2)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in offline deterministic simulation mode (no API key required)"
    )
    parser.add_argument(
        "--deliberate-error",
        type=str,
        choices=["PHD_JARGON", "MISSING_ANALOGY", "INCOMPLETE_STRUCTURE"],
        default=None,
        help="Inject a deliberate pedagogical/technical flaw on Draft 1 to demonstrate evaluator rejection"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override LLM model name (default from config/env)"
    )

    args = parser.parse_args()

    ConsoleDisplay.print_header(
        "Self-Evaluating Lesson Content Generator",
        f"Target Audience: 12th-grade graduate from India (Regional-medium, zero AI background)\n"
        f"Topic: {args.topic} | Max Retries: {args.retries} | Mock Mode: {args.mock}"
    )

    # Initialize subsystems
    llm_client = LLMClient(model=args.model, mock_mode=args.mock)
    generator = LessonGenerator(llm_client=llm_client)
    evaluator = ContentEvaluator(llm_client=llm_client)
    memory_manager = EvolutionMemoryManager()

    orchestrator = ContentGraphOrchestrator(
        generator=generator,
        evaluator=evaluator,
        memory_manager=memory_manager
    )

    try:
        final_state = orchestrator.run(
            topic=args.topic,
            max_retries=args.retries,
            deliberate_error_type=args.deliberate_error
        )

        if final_state["is_final_approved"]:
            console.print(
                "\n[bold green]✓ SUCCESS: Approved lesson content generated and saved to final_lesson_document.md![/bold green]"
            )
            console.print(
                "[bold cyan]Audit trail saved to logs/rejection_log_summary.json[/bold cyan]\n"
            )
            sys.exit(0)
        else:
            console.print(
                "\n[bold red]✗ PIPELINE HALTED: Content failed to clear all hard checkpoints within retry limit.[/bold red]"
            )
            sys.exit(1)

    except KeyboardInterrupt:
        console.print("\n[yellow]Execution halted by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error during execution: {e}")
        console.print(f"\n[bold red]Fatal Error: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

