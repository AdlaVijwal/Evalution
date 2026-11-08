"""Unit tests for the Self-Evolving Memory System."""

import unittest
import tempfile
from pathlib import Path
from src.schemas import EvaluationReport, RubricCheckResult, CheckpointEnum
from src.memory.evolution_manager import EvolutionMemoryManager


class TestMemoryEvolution(unittest.TestCase):

    def test_memory_persistence_and_evolution(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "test_store.json"
            manager = EvolutionMemoryManager(store_path=store_path)

            # Initial guardrails
            initial_rules = manager.get_active_guardrails()
            self.assertGreaterEqual(len(initial_rules), 3)

            # Simulate repeat failure in BEGINNER_VOCABULARY
            failed_report_1 = EvaluationReport(
                overall_passed=False,
                checks=[
                    RubricCheckResult(
                        checkpoint=CheckpointEnum.BEGINNER_VOCABULARY,
                        passed=False,
                        reasoning="Readability too complex"
                    )
                ],
                failed_checkpoints=[CheckpointEnum.BEGINNER_VOCABULARY]
            )
            failed_report_2 = EvaluationReport(
                overall_passed=False,
                checks=[
                    RubricCheckResult(
                        checkpoint=CheckpointEnum.BEGINNER_VOCABULARY,
                        passed=False,
                        reasoning="Grade level exceeded"
                    )
                ],
                failed_checkpoints=[CheckpointEnum.BEGINNER_VOCABULARY]
            )

            manager.record_run(
                topic="Test Topic 1",
                total_iterations=1,
                final_passed=False,
                reports=[failed_report_1, failed_report_2]
            )

            # Re-instantiate from the same disk file to verify persistence
            new_manager = EvolutionMemoryManager(store_path=store_path)
            updated_rules = new_manager.get_active_guardrails()

            # Should have learned and added the new rule
            self.assertTrue(any("Rule 4 (Learned)" in r for r in updated_rules))
            data = new_manager.load_data()
            self.assertEqual(data["total_runs_recorded"], 1)
            self.assertEqual(data["historical_failure_counts"]["BEGINNER_VOCABULARY"], 2)


if __name__ == "__main__":
    unittest.main()
