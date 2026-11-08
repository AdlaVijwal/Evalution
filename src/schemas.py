"""Pydantic v2 schemas for the Content Systems Agentic Generator."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CheckpointEnum(str, Enum):
    """The 6 hard pass/fail checkpoints mandated by the assessment rubric."""
    ACCURACY_AND_GROUNDING = "ACCURACY_AND_GROUNDING"
    BEGINNER_VOCABULARY = "BEGINNER_VOCABULARY"
    ANALOGY_AND_EXAMPLE = "ANALOGY_AND_EXAMPLE"
    NO_UNEXPLAINED_JARGON = "NO_UNEXPLAINED_JARGON"
    KEY_POINTS_COVERAGE = "KEY_POINTS_COVERAGE"
    COHERENT_TEACHING_FLOW = "COHERENT_TEACHING_FLOW"


class RubricCheckResult(BaseModel):
    """Result of evaluating a single rubric checkpoint. Strictly binary: NO partial credit."""
    checkpoint: CheckpointEnum
    passed: bool = Field(..., description="Binary PASS/FAIL. Must be True or False.")
    reasoning: str = Field(..., description="Explicit rationale for the pass or fail verdict.")
    offending_snippet: Optional[str] = Field(
        None, description="Exact phrase or sentence that triggered failure, if any."
    )
    prescriptive_action: Optional[str] = Field(
        None, description="Direct instruction on how to rectify the issue on retry."
    )


class EvaluationReport(BaseModel):
    """Aggregated evaluation across all checkpoints."""
    overall_passed: bool = Field(..., description="True ONLY if 100% of checkpoints pass.")
    checks: List[RubricCheckResult] = Field(..., description="Results for each checkpoint.")
    failed_checkpoints: List[CheckpointEnum] = Field(
        default_factory=list, description="List of checkpoints that failed."
    )
    rejection_reasons: List[str] = Field(
        default_factory=list, description="Summary of reasons for rejection."
    )
    actionable_feedback_prompt: str = Field(
        default="", description="Consolidated feedback fed back to the generator on retry."
    )


class LessonDraft(BaseModel):
    """Structured lesson content created by the generator."""
    topic: str
    iteration: int = 1
    title: str
    target_audience_callout: str = "Specially written for beginners with simple English & relatable examples"
    hook_and_analogy: str
    what_is_it: str
    why_it_matters: str
    how_it_works: str
    quick_summary_takeaway: str
    full_content_markdown: str


class RejectionLogEntry(BaseModel):
    """Audit log entry capturing what failed, why, and what was changed on retry."""
    iteration: int
    failed_checks: List[str]
    why_it_failed: List[str]
    what_was_changed_on_retry: str
    timestamp: str


class EvolutionRule(BaseModel):
    """Learned pattern persisted across runs to sharpen prompts/rubrics."""
    id: str
    failed_checkpoint: CheckpointEnum
    anti_pattern: str
    prescribed_guardrail: str
    occurrence_count: int = 1
    last_triggered_topic: str


class AgentState(BaseModel):
    """State of the LangGraph agentic loop."""
    topic: str
    iteration: int = 0
    max_retries: int = 2
    current_draft: Optional[LessonDraft] = None
    draft_history: List[LessonDraft] = Field(default_factory=list)
    evaluation_reports: List[EvaluationReport] = Field(default_factory=list)
    rejection_log: List[RejectionLogEntry] = Field(default_factory=list)
    is_final_approved: bool = False
    status_message: str = "Initialized"
    learned_evolution_rules: List[str] = Field(default_factory=list)

