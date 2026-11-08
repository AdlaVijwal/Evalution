"""Integration tests for deliberate error injection and recovery."""

import unittest
import tempfile
from pathlib import Path
from src.utils.llm_client import LLMClient
from src.generator.generator import LessonGenerator
from src.evaluator.evaluator import ContentEvaluator
from src.memory.evolution_manager import EvolutionMemoryManager
from src.graph.workflow import ContentGraphOrchestrator


class TestDeliberateErrors(unittest.TestCase):

    def test_deliberate_phd_jargon_caught(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            memory = EvolutionMemoryManager(store_path=Path(tmpdir) / "test_store.json")
            llm = LLMClient(mock_mode=True)
            generator = LessonGenerator(llm_client=llm)
            evaluator = ContentEvaluator(llm_client=llm)

            orchestrator = ContentGraphOrchestrator(
                generator=generator,
                evaluator=evaluator,
                memory_manager=memory
            )

            state = orchestrator.run(
                topic="Introduction to RAG",
                max_retries=1
            )

            self.assertGreaterEqual(state["iteration"], 1)
            self.assertIn("evaluation_reports", state)
            self.assertGreaterEqual(len(state["draft_history"]), 1)

    def test_deliberate_jargon_causes_rejection(self):
        from src.schemas import LessonDraft, CheckpointEnum
        evaluator = ContentEvaluator(llm_client=LLMClient(mock_mode=True))
        
        jargon_draft = LessonDraft(
            topic="Introduction to RAG",
            iteration=1,
            title="Complex RAG Architecture",
            hook_and_analogy="Let us discuss dense vector embeddings in high-dimensional latent space.",
            what_is_it="RAG uses cosine similarity metric to retrieve nearest neighbors.",
            why_it_matters="It minimizes cross-entropy loss across non-parametric memory.",
            how_it_works="Tokens are projected through stochastic gradient descent manifolds.",
            quick_summary_takeaway="Embeddings optimize parametric representations.",
            full_content_markdown="This lesson relies on high-dimensional vector space and cosine similarity metric."
        )

        report = evaluator.evaluate(jargon_draft)
        self.assertFalse(report.overall_passed)
        self.assertIn(CheckpointEnum.NO_UNEXPLAINED_JARGON, report.failed_checkpoints)


if __name__ == "__main__":
    unittest.main()
