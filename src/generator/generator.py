"""Generator Agent implementation."""

import logging
from typing import List, Optional, Dict, Any
from src.schemas import LessonDraft, EvaluationReport
from src.generator.prompts import (
    SYSTEM_GENERATOR_BASE,
    REFINEMENT_PROMPT_WRAPPER,
    DELIBERATE_ERROR_INJECTION_PROMPTS
)
from src.utils.llm_client import LLMClient

logger = logging.getLogger("ContentSystem.Generator")


class LessonGenerator:
    """Agent responsible for crafting beginner-friendly educational lessons."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def generate_draft(
        self,
        topic: str,
        iteration: int = 1,
        previous_report: Optional[EvaluationReport] = None,
        learned_rules: Optional[List[str]] = None,
        deliberate_error_type: Optional[str] = None
    ) -> LessonDraft:
        """Generate a complete lesson draft, integrating feedback or deliberate errors."""
        system_prompt = SYSTEM_GENERATOR_BASE

        if learned_rules:
            rules_block = "\n\nCRITICAL HISTORICAL LESSONS LEARNED (Self-Evolving Memory):\n"
            for rule in learned_rules:
                rules_block += f"- ⚡ {rule}\n"
            system_prompt += rules_block

        user_prompt = f"Topic to teach: '{topic}'. Remember: The learner starts from zero."

        if deliberate_error_type and deliberate_error_type in DELIBERATE_ERROR_INJECTION_PROMPTS:
            logger.warning(f"Injecting deliberate error mode: {deliberate_error_type}")
            user_prompt += "\n" + DELIBERATE_ERROR_INJECTION_PROMPTS[deliberate_error_type]
        elif previous_report and not previous_report.overall_passed:
            failed_str = ", ".join([c.value for c in previous_report.failed_checkpoints])
            reasons_str = "\n".join([f"• {r}" for r in previous_report.rejection_reasons])
            feedback_block = REFINEMENT_PROMPT_WRAPPER.format(
                failed_checkpoints=failed_str,
                rejection_reasons=reasons_str,
                actionable_feedback=previous_report.actionable_feedback_prompt
            )
            user_prompt += "\n" + feedback_block

        logger.info(f"Generating lesson draft v{iteration} for topic: '{topic}'...")
        payload = self.llm.generate_json(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6 if iteration == 1 else 0.4
        )

        title = payload.get("title") or payload.get("Title") or f"Introduction to {topic}"
        hook = payload.get("hook_and_analogy") or payload.get("hook") or payload.get("analogy") or ""
        what_is = payload.get("what_is_it") or payload.get("what_is") or payload.get("definition") or ""
        why_matters = payload.get("why_it_matters") or payload.get("why_matters") or payload.get("importance") or ""
        how_works = payload.get("how_it_works") or payload.get("how_works") or payload.get("mechanics") or ""
        takeaway = payload.get("quick_summary_takeaway") or payload.get("takeaway") or payload.get("summary") or ""

        # Compile cohesive markdown presentation
        full_md = f"""# {title}
*A beginner's guide for curious minds starting their AI journey.*

---

## 🎯 1. The Story: How to Understand This Instantly
{hook}

---

## 💡 2. What Exactly Is It?
{what_is}

---

## 🚀 3. Why Does This Matter in the Real World?
{why_matters}

---

## ⚙️ 4. How Does It Work? (Step-by-Step)
{how_works}

---

## 🧠 5. Raju Bhaiya's Golden Takeaway
{takeaway}
"""

        return LessonDraft(
            topic=topic,
            iteration=iteration,
            title=title,
            hook_and_analogy=hook,
            what_is_it=what_is,
            why_it_matters=why_matters,
            how_it_works=how_works,
            quick_summary_takeaway=takeaway,
            full_content_markdown=full_md
        )

