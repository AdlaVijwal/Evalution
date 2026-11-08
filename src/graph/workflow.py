"""LangGraph StateGraph orchestration for the Generate -> Evaluate -> Regenerate loop."""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Literal, Optional
from langgraph.graph import StateGraph, START, END

from src.graph.state import ContentState
from src.generator.generator import LessonGenerator
from src.evaluator.evaluator import ContentEvaluator
from src.memory.evolution_manager import EvolutionMemoryManager
from src.schemas import RejectionLogEntry
from src.utils.console_display import ConsoleDisplay
from src.config import OUTPUT_DOCUMENT_PATH, REJECTION_LOG_PATH

logger = logging.getLogger("ContentSystem.Workflow")


class ContentGraphOrchestrator:
    """Encapsulates the LangGraph cyclical state machine."""

    def __init__(
        self,
        generator: LessonGenerator,
        evaluator: ContentEvaluator,
        memory_manager: EvolutionMemoryManager
    ):
        self.generator = generator
        self.evaluator = evaluator
        self.memory = memory_manager
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        builder = StateGraph(ContentState)

        # Register nodes
        builder.add_node("generate", self.generate_node)
        builder.add_node("evaluate", self.evaluate_node)
        builder.add_node("prepare_retry", self.prepare_retry_node)
        builder.add_node("finalize", self.finalize_node)
        builder.add_node("terminate_max_retries", self.terminate_max_retries_node)

        # Set edges
        builder.add_edge(START, "generate")
        builder.add_edge("generate", "evaluate")

        # Conditional routing after evaluation
        builder.add_conditional_edges(
            "evaluate",
            self.route_evaluation_verdict,
            {
                "pass": "finalize",
                "retry": "prepare_retry",
                "halt_max_retries": "terminate_max_retries"
            }
        )

        builder.add_edge("prepare_retry", "generate")
        builder.add_edge("finalize", END)
        builder.add_edge("terminate_max_retries", END)

        return builder.compile()

    def generate_node(self, state: ContentState) -> Dict[str, Any]:
        """Node 1: Generate a lesson draft."""
        iteration = state["iteration"] + 1
        topic = state["topic"]
        rules = state.get("learned_evolution_rules", [])

        previous_report = None
        if state["evaluation_reports"]:
            previous_report = state["evaluation_reports"][-1]

        ConsoleDisplay.print_stage(
            f"Draft Generation (Iteration {iteration})",
            f"Synthesizing lesson for topic: '{topic}'"
        )
        if rules:
            ConsoleDisplay.print_evolution_notice(rules)

        # Only inject deliberate error on iteration 1 if set
        delib_error = state.get("deliberate_error_type") if iteration == 1 else None

        draft = self.generator.generate_draft(
            topic=topic,
            iteration=iteration,
            previous_report=previous_report,
            learned_rules=rules,
            deliberate_error_type=delib_error
        )

        return {
            "iteration": iteration,
            "current_draft": draft,
            "status_message": f"Draft iteration {iteration} created."
        }

    def evaluate_node(self, state: ContentState) -> Dict[str, Any]:
        """Node 2: Evaluate the current draft against all 6 hard checkpoints."""
        draft = state["current_draft"]
        iteration = state["iteration"]

        ConsoleDisplay.print_stage(
            f"Evaluation Audit (Iteration {iteration})",
            "Checking 6 hard pass/fail checkpoints (Zero Partial Credit)"
        )

        report = self.evaluator.evaluate(draft)
        ConsoleDisplay.print_evaluation_report(report, iteration)

        # Update lists immutably
        draft_hist = list(state.get("draft_history", []))
        draft_hist.append(draft)

        eval_reports = list(state.get("evaluation_reports", []))
        eval_reports.append(report)

        return {
            "draft_history": draft_hist,
            "evaluation_reports": eval_reports,
            "is_final_approved": report.overall_passed,
            "status_message": "Draft passed audit." if report.overall_passed else "Draft failed audit."
        }

    def route_evaluation_verdict(
        self, state: ContentState
    ) -> Literal["pass", "retry", "halt_max_retries"]:
        """Conditional routing logic."""
        latest_report = state["evaluation_reports"][-1]
        if latest_report.overall_passed:
            return "pass"

        # Check if we still have retry budget (max 1-2 retries)
        if state["iteration"] <= state["max_retries"]:
            return "retry"

        return "halt_max_retries"

    def prepare_retry_node(self, state: ContentState) -> Dict[str, Any]:
        """Node 3: Log rejection reasons and prepare explicit guidance for retry."""
        iteration = state["iteration"]
        latest_report = state["evaluation_reports"][-1]

        ConsoleDisplay.print_stage(
            f"Rejection Diagnostics & Feedback (Iteration {iteration})",
            "Synthesizing feedback for Generator refinement"
        )

        entry = RejectionLogEntry(
            iteration=iteration,
            failed_checks=[c.value for c in latest_report.failed_checkpoints],
            why_it_failed=latest_report.rejection_reasons,
            what_was_changed_on_retry=latest_report.actionable_feedback_prompt or "Refining vocabulary and examples.",
            timestamp=datetime.now().isoformat()
        )
        ConsoleDisplay.print_rejection_log_entry(entry)

        rejection_log = list(state.get("rejection_log", []))
        rejection_log.append(entry)

        return {
            "rejection_log": rejection_log,
            "status_message": f"Iteration {iteration} logged to Rejection Log. Transitioning to regeneration."
        }

    def finalize_node(self, state: ContentState) -> Dict[str, Any]:
        """Node 4: Content passed all checkpoints. Finalize deliverables and update memory."""
        final_draft = state["current_draft"]
        ConsoleDisplay.print_stage("SHIP GATE APPROVED", "Saving publication-ready deliverables")
        ConsoleDisplay.print_lesson_preview(final_draft)

        # 1. Write final lesson markdown document
        with open(OUTPUT_DOCUMENT_PATH, "w", encoding="utf-8") as f:
            f.write(final_draft.full_content_markdown)
        logger.info(f"Saved approved lesson to {OUTPUT_DOCUMENT_PATH}")

        # 2. Write structured rejection log
        rejection_summary = [entry.model_dump() for entry in state["rejection_log"]]
        with open(REJECTION_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(rejection_summary, f, indent=2)
        logger.info(f"Saved rejection log to {REJECTION_LOG_PATH}")

        # 3. Update persistent memory
        self.memory.record_run(
            topic=state["topic"],
            total_iterations=state["iteration"],
            final_passed=True,
            reports=state["evaluation_reports"]
        )

        return {
            "is_final_approved": True,
            "status_message": "Pipeline completed successfully. Content ready for publication."
        }

    def terminate_max_retries_node(self, state: ContentState) -> Dict[str, Any]:
        """Node 5: Max retries exceeded. Terminate cleanly and log failure."""
        logger.warning(f"Maximum retry limit ({state['max_retries']}) reached without full approval.")
        ConsoleDisplay.print_stage("PIPELINE HALT", "Max retry budget exhausted. Loop terminated safely.")

        rejection_summary = [entry.model_dump() for entry in state["rejection_log"]]
        with open(REJECTION_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(rejection_summary, f, indent=2)

        self.memory.record_run(
            topic=state["topic"],
            total_iterations=state["iteration"],
            final_passed=False,
            reports=state["evaluation_reports"]
        )

        return {
            "is_final_approved": False,
            "status_message": "Terminated: Reached maximum allowed retries."
        }

    def run(
        self,
        topic: str,
        max_retries: int = 2,
        deliberate_error_type: Optional[str] = None
    ) -> ContentState:
        """Execute the LangGraph workflow from start to finish."""
        initial_rules = self.memory.get_active_guardrails()

        initial_state: ContentState = {
            "topic": topic,
            "iteration": 0,
            "max_retries": max_retries,
            "current_draft": None,
            "draft_history": [],
            "evaluation_reports": [],
            "rejection_log": [],
            "is_final_approved": False,
            "status_message": "Initialized",
            "learned_evolution_rules": initial_rules,
            "deliberate_error_type": deliberate_error_type
        }

        result = self.graph.invoke(initial_state)
        return result
