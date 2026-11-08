"""LangGraph State definition for the Content Generation Pipeline."""

from typing import List, Optional, Dict, Any
from typing_extensions import TypedDict
from src.schemas import (
    LessonDraft,
    EvaluationReport,
    RejectionLogEntry
)


class ContentState(TypedDict):
    """Shared state dictionary passed across LangGraph nodes."""
    topic: str
    iteration: int
    max_retries: int
    current_draft: Optional[LessonDraft]
    draft_history: List[LessonDraft]
    evaluation_reports: List[EvaluationReport]
    rejection_log: List[RejectionLogEntry]
    is_final_approved: bool
    status_message: str
    learned_evolution_rules: List[str]
    deliberate_error_type: Optional[str]

