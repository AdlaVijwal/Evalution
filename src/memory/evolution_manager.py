"""Self-Evolving Memory System that persists across runs and sharpens prompts & rubrics."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.schemas import EvaluationReport, CheckpointEnum
from src.config import MEMORY_STORE_PATH

logger = logging.getLogger("ContentSystem.Memory")

DEFAULT_EVOLUTION_SEED = {
    "version": "1.0",
    "total_runs_recorded": 0,
    "historical_failure_counts": {
        "ACCURACY_AND_GROUNDING": 0,
        "BEGINNER_VOCABULARY": 0,
        "ANALOGY_AND_EXAMPLE": 0,
        "NO_UNEXPLAINED_JARGON": 0,
        "KEY_POINTS_COVERAGE": 0,
        "COHERENT_TEACHING_FLOW": 0
    },
    "learned_guardrails": [
        "Rule 1: Never introduce 'vector database' without immediately explaining it as 'a smart digital filing cabinet'.",
        "Rule 2: Keep average sentence length under 15 words for regional-medium learners.",
        "Rule 3: Always carry the Indian everyday analogy (e.g. open-book exam) into the 'How it works' technical steps."
    ],
    "run_history": []
}


class EvolutionMemoryManager:
    """Manages cross-run memory, failure pattern clustering, and self-evolving guardrail generation."""

    def __init__(self, store_path: Optional[Path] = None):
        self.store_path = store_path or MEMORY_STORE_PATH
        self._ensure_store()

    def _ensure_store(self):
        """Initialize persistent storage if not already present."""
        if not self.store_path.parent.exists():
            self.store_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.store_path.exists():
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_EVOLUTION_SEED, f, indent=2)
            logger.info(f"Initialized fresh evolution memory store at {self.store_path}")

    def load_data(self) -> Dict[str, Any]:
        """Read state from JSON store."""
        try:
            with open(self.store_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading memory store: {e}. Resetting to seed.")
            return DEFAULT_EVOLUTION_SEED.copy()

    def save_data(self, data: Dict[str, Any]):
        """Persist state to JSON store."""
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_active_guardrails(self) -> List[str]:
        """Fetch sharpened prompt guardrails to be dynamically injected into the Generator."""
        data = self.load_data()
        return data.get("learned_guardrails", [])

    def record_run(
        self,
        topic: str,
        total_iterations: int,
        final_passed: bool,
        reports: List[EvaluationReport]
    ):
        """Record evaluation feedback from this run, learn from failures, and sharpen rules."""
        data = self.load_data()
        data["total_runs_recorded"] = data.get("total_runs_recorded", 0) + 1

        counts = data.get("historical_failure_counts", {})
        new_failures_detected = []

        # Tally failures across all draft iterations
        for rep in reports:
            for failed_cp in rep.failed_checkpoints:
                key = failed_cp.value if hasattr(failed_cp, "value") else str(failed_cp)
                counts[key] = counts.get(key, 0) + 1
                new_failures_detected.append(key)

        data["historical_failure_counts"] = counts

        # Self-evolution logic: Synthesize new guardrails if patterns emerge
        guardrails = data.get("learned_guardrails", [])
        
        if counts.get("BEGINNER_VOCABULARY", 0) >= 2 and not any("readability" in g.lower() for g in guardrails):
            guardrails.append(
                "Rule 4 (Learned): High syllable density detected across runs. Avoid Latinate or academic prefixes; prefer Anglo-Saxon root words."
            )
            logger.info("⚡ Self-Evolving Engine: Added new rule for BEGINNER_VOCABULARY based on historical trends.")

        if counts.get("NO_UNEXPLAINED_JARGON", 0) >= 2 and not any("acronyms" in g.lower() for g in guardrails):
            guardrails.append(
                "Rule 5 (Learned): Learner struggles with acronyms. Spell out RAG as 'Retrieval (Searching) + Augmented (Adding) + Generation (Creating)' repeatedly."
            )
            logger.info("⚡ Self-Evolving Engine: Added new rule for NO_UNEXPLAINED_JARGON based on historical trends.")

        data["learned_guardrails"] = guardrails

        # Append run log
        run_entry = {
            "timestamp": datetime.now().isoformat(),
            "topic": topic,
            "total_iterations": total_iterations,
            "final_passed": final_passed,
            "failures_encountered": new_failures_detected
        }
        data.setdefault("run_history", []).append(run_entry)

        self.save_data(data)
        logger.info(f"Updated evolution store at {self.store_path}. Total runs: {data['total_runs_recorded']}")

