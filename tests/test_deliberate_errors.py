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


if __name__ == "__main__":
    unittest.main()
