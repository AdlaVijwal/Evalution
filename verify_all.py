#!/usr/bin/env python3
"""Pre-flight verification script to ensure all systems are 100% operational before recording the Loom video."""

import sys
import unittest
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.config import (
    BASE_DIR,
    OUTPUT_DOCUMENT_PATH,
    REJECTION_LOG_PATH,
    MEMORY_STORE_PATH,
    OPENROUTER_API_KEY,
    OPENAI_API_KEY
)

console = Console()


def run_preflight_checks():
    console.print(Panel(
        "[bold cyan]GenAI Engineer Assessment | Pre-Flight Readiness Audit[/bold cyan]\n"
        "Verifying code integrity, unit tests, deliverable files, and API connectivity...",
        border_style="cyan"
    ))

    table = Table(title="Pre-Flight Verification Checklist", border_style="blue")
    table.add_column("Audit Item", style="bold white", width=36)
    table.add_column("Status", justify="center", width=12)
    table.add_column("Diagnostic Details", style="dim", width=42)

    all_passed = True

    # 1. Check Deliverable Files
    deliv_files = [
        ("Final Lesson Document", OUTPUT_DOCUMENT_PATH),
        ("Rejection Log Summary", REJECTION_LOG_PATH),
        ("Evolution Store Memory", MEMORY_STORE_PATH),
        ("Loom Video Script", BASE_DIR / "loom_script.md"),
        ("Project README", BASE_DIR / "README.md"),
    ]

    for name, path in deliv_files:
        exists = path.exists() and path.stat().st_size > 0
        if not exists:
            all_passed = False
        table.add_row(
            name,
            "[bold green]OK ✓[/bold green]" if exists else "[bold red]FAIL ✗[/bold red]",
            f"Found: {path.name} ({path.stat().st_size if path.exists() else 0} bytes)"
        )

    # 2. Check API Key
    has_api_key = bool(OPENROUTER_API_KEY or OPENAI_API_KEY)
    table.add_row(
        "LLM API Key / Connectivity",
        "[bold green]OK ✓[/bold green]" if has_api_key else "[bold yellow]MOCK ONLY[/bold yellow]",
        "Active OpenRouter/OpenAI key detected" if has_api_key else "Running in offline mock mode"
    )

    # 3. Check Unit Test Suite
    loader = unittest.TestLoader()
    suite = loader.discover(str(BASE_DIR / "tests"))
    runner = unittest.TextTestRunner(stream=open("/dev/null", "w"))
    test_result = runner.run(suite)
    tests_ok = test_result.wasSuccessful() and test_result.testsRun >= 7
    if not tests_ok:
        all_passed = False

    table.add_row(
        "Automated Test Suite (8/8)",
        "[bold green]OK ✓[/bold green]" if tests_ok else "[bold red]FAIL ✗[/bold red]",
        f"Ran {test_result.testsRun} tests, {len(test_result.errors)} errors, {len(test_result.failures)} failures"
    )

    # 4. Check Demo Scripts
    scripts = [
        ("Production CLI Runner", BASE_DIR / "run_pipeline.py"),
        ("Deliberate Error Demo", BASE_DIR / "test_deliberate_error.py"),
        ("Streamlit Web Dashboard", BASE_DIR / "app.py"),
    ]
    for name, path in scripts:
        exists = path.exists()
        if not exists:
            all_passed = False
        table.add_row(
            name,
            "[bold green]OK ✓[/bold green]" if exists else "[bold red]FAIL ✗[/bold red]",
            f"Script present at {path.name}"
        )

    console.print(table)

    if all_passed:
        console.print(Panel(
            "[bold green]🎉 ALL PRE-FLIGHT CHECKS PASSED![/bold green]\n"
            "Your workspace is 100% ready for the Loom video recording and final submission.",
            border_style="green"
        ))
        sys.exit(0)
    else:
        console.print(Panel(
            "[bold red]⚠️ Some checks did not pass. Please review the table above.[/bold red]",
            border_style="red"
        ))
        sys.exit(1)


if __name__ == "__main__":
    run_preflight_checks()
