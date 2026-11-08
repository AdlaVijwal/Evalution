"""Dual-Engine Evaluator combining deterministic rules and semantic LLM judging."""

import logging
from typing import List, Optional
from src.schemas import (
    LessonDraft,
    EvaluationReport,
    RubricCheckResult,
    CheckpointEnum
)
from src.evaluator.deterministic_rules import run_deterministic_evaluations
from src.evaluator.llm_judge import LLMJudge
from src.utils.llm_client import LLMClient

logger = logging.getLogger("ContentSystem.Evaluator")


class ContentEvaluator:
    """Master evaluator ensuring 100% adherence to the rubric with zero partial credit."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_judge = LLMJudge(llm_client=llm_client)

    def evaluate(self, draft: LessonDraft) -> EvaluationReport:
        """Run all 6 checkpoints across deterministic and LLM engines."""
        logger.info(f"Auditing Lesson Draft v{draft.iteration} across all 6 rubric dimensions...")

        det_results = run_deterministic_evaluations(
            text=draft.full_content_markdown,
            what_is_it=draft.what_is_it,
            why_it_matters=draft.why_it_matters,
            how_it_works=draft.how_it_works,
            hook_and_analogy=draft.hook_and_analogy
        )
        llm_results = self.llm_judge.evaluate_draft(draft)

        all_checks: List[RubricCheckResult] = det_results + llm_results

        enum_order = list(CheckpointEnum)
        all_checks.sort(key=lambda c: enum_order.index(c.checkpoint))

        failed_checks = [c.checkpoint for c in all_checks if not c.passed]
        overall_passed = len(failed_checks) == 0

        rejection_reasons = []
        prescriptive_feedback = []

        for check in all_checks:
            if not check.passed:
                rejection_reasons.append(f"[{check.checkpoint.value}] {check.reasoning}")
                if check.prescriptive_action:
                    prescriptive_feedback.append(
                        f"For {check.checkpoint.value}: {check.prescriptive_action}"
                    )

        feedback_prompt = "\n".join(prescriptive_feedback)

        logger.info(
            f"Audit Complete: Overall {'PASSED' if overall_passed else 'REJECTED'} "
            f"({len(all_checks) - len(failed_checks)}/{len(all_checks)} passed)."
        )

        return EvaluationReport(
            overall_passed=overall_passed,
            checks=all_checks,
            failed_checkpoints=failed_checks,
            rejection_reasons=rejection_reasons,
            actionable_feedback_prompt=feedback_prompt
        )

