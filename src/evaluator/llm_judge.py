"""LLM-as-a-Judge module for semantic pedagogical checks."""

import logging
from typing import List, Dict, Any, Optional
from src.schemas import CheckpointEnum, RubricCheckResult, LessonDraft
from src.utils.llm_client import LLMClient

logger = logging.getLogger("ContentSystem.LLMJudge")

JUDGE_SYSTEM_PROMPT = """You are an ultra-strict Chief Pedagogical Auditor for an AI education company in India.
Your mission is to evaluate whether a lesson on AI is truly fit to ship to a 12th-grade graduate from a non-English-medium background.

You MUST evaluate the content against 3 strict binary checkpoints.
CRITICAL RULE: NO PARTIAL CREDIT. Each checkpoint is either a 100% PASS (true) or an instant FAIL (false).
If there is any ambiguity, confusion, or lack of grounding, you MUST mark it FALSE.

THE 3 CHECKPOINTS TO JUDGE:

1. ACCURACY_AND_GROUNDING:
   - Does it accurately explain RAG (Retrieval-Augmented Generation)?
   - It MUST clearly convey that RAG searches external documents (retrieval), inserts that fresh context into the prompt (augmentation), and generates the answer.
   - FAIL if it confuses RAG with fine-tuning/training weights, or treats it as mere web browsing without explaining the injection into the prompt.

2. ANALOGY_AND_EXAMPLE:
   - Does the lesson teach through a tangible, relatable everyday example?
   - For an Indian 12th-grade student, relatable examples include: open-book board exams, school libraries, Kirana shop khata ledger, asking a smart friend with fresh notes.
   - FAIL if it relies on abstract Silicon Valley definitions, lacks a concrete scenario, or drops the analogy halfway through.

3. COHERENT_TEACHING_FLOW:
   - Does the lesson have a natural, progressive storytelling flow?
   - Flow order MUST be: Engaging Real-World Hook ➔ Why normal AI struggles (the problem) ➔ Clear Definition ➔ Step-by-Step Mechanics ➔ Memorable Summary.
   - FAIL if concepts jump abruptly, if sections contradict each other, or if it reads like disconnected bullet points.

OUTPUT FORMAT:
You MUST respond with valid JSON containing results for these 3 keys:
{
  "ACCURACY_AND_GROUNDING": {
    "passed": true/false,
    "reasoning": "Explicit explanation",
    "offending_snippet": "Quote causing failure if any, else null",
    "prescriptive_action": "Exact correction needed if any, else null"
  },
  "ANALOGY_AND_EXAMPLE": {
    "passed": true/false,
    "reasoning": "Explicit explanation",
    "offending_snippet": "Quote causing failure if any, else null",
    "prescriptive_action": "Exact correction needed if any, else null"
  },
  "COHERENT_TEACHING_FLOW": {
    "passed": true/false,
    "reasoning": "Explicit explanation",
    "offending_snippet": "Quote causing failure if any, else null",
    "prescriptive_action": "Exact correction needed if any, else null"
  }
}
"""


class LLMJudge:
    """Evaluates semantic, pedagogical, and conceptual checkpoints using LLM reasoning."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def evaluate_draft(self, draft: LessonDraft) -> List[RubricCheckResult]:
        """Perform strict semantic evaluation on the draft."""
        user_prompt = f"""EVALUATE THIS LESSON DRAFT:

TITLE: {draft.title}

1. HOOK & ANALOGY:
{draft.hook_and_analogy}

2. WHAT IS IT:
{draft.what_is_it}

3. WHY IT MATTERS:
{draft.why_it_matters}

4. HOW IT WORKS:
{draft.how_it_works}

5. QUICK SUMMARY & TAKEAWAY:
{draft.quick_summary_takeaway}

Remember: Be uncompromising. Binary PASS (true) or FAIL (false) only. No partial credit!"""

        logger.info("Executing LLM-as-a-Judge semantic rubric audit...")
        raw_res = self.llm.generate_json(
            system_prompt=JUDGE_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.1  # Low temperature for deterministic grading
        )

        # Normalize keys to uppercase for bulletproof case-insensitivity
        normalized_res = {str(k).upper(): v for k, v in raw_res.items()}

        results = []
        mapping = {
            "ACCURACY_AND_GROUNDING": CheckpointEnum.ACCURACY_AND_GROUNDING,
            "ANALOGY_AND_EXAMPLE": CheckpointEnum.ANALOGY_AND_EXAMPLE,
            "COHERENT_TEACHING_FLOW": CheckpointEnum.COHERENT_TEACHING_FLOW
        }

        for key, enum_val in mapping.items():
            check_data = normalized_res.get(key, {})
            if isinstance(check_data, dict):
                norm_check = {str(k).lower(): v for k, v in check_data.items()}
            else:
                norm_check = {}

            passed = bool(norm_check.get("passed", False))
            reasoning = norm_check.get("reasoning", "No explicit reasoning provided.")
            snippet = norm_check.get("offending_snippet")
            action = norm_check.get("prescriptive_action")

            results.append(
                RubricCheckResult(
                    checkpoint=enum_val,
                    passed=passed,
                    reasoning=reasoning,
                    offending_snippet=snippet if not passed else None,
                    prescriptive_action=action if not passed else None
                )
            )

        return results

