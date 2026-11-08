"""Unit tests for the Evaluation Engine and Rubric Checkpoints."""

import unittest
from src.schemas import CheckpointEnum, LessonDraft
from src.evaluator.deterministic_rules import (
    count_syllables,
    calculate_readability_metrics,
    check_forbidden_jargon,
    run_deterministic_evaluations
)
from src.evaluator.evaluator import ContentEvaluator
from src.utils.llm_client import LLMClient


class TestEvaluator(unittest.TestCase):

    def test_syllable_counter(self):
        self.assertEqual(count_syllables("AI"), 1)
        self.assertEqual(count_syllables("book"), 1)
        self.assertGreaterEqual(count_syllables("retrieval"), 3)
        self.assertGreaterEqual(count_syllables("generation"), 4)

    def test_forbidden_jargon_detection(self):
        # Clean text with grounded explanation
        clean_text = "Think of RAG like an open-book exam where you find information."
        passed, flagged = check_forbidden_jargon(clean_text)
        self.assertTrue(passed)
        self.assertEqual(len(flagged), 0)

        # Violating text with PhD jargon
        bad_text = "The system projects tokens into a high-dimensional vector space with cosine similarity metric."
        passed, flagged = check_forbidden_jargon(bad_text)
        self.assertFalse(passed)
        self.assertGreaterEqual(len(flagged), 1)

    def test_readability_calculator(self):
        # Simple sentences
        simple_text = "RAG helps AI. It gives AI a book. The AI reads the book. Then the AI answers."
        grade, ease, s_count, w_count = calculate_readability_metrics(simple_text)
        self.assertLessEqual(grade, 6.0)
        self.assertGreaterEqual(ease, 70.0)

        # Complex academic text
        complex_text = "The stochastic optimization manifold facilitates non-parametric representations through epistemological paradigms."
        grade, ease, s_count, w_count = calculate_readability_metrics(complex_text)
        self.assertGreater(grade, 12.0)

    def test_deterministic_evaluations_zero_partial_credit(self):
        # Incomplete draft missing 'why_it_matters'
        results = run_deterministic_evaluations(
            text="Sample text",
            what_is_it="This is an explanation of what it is with more than fifty characters to pass the basic length threshold.",
            why_it_matters="",  # Empty!
            how_it_works="This is an explanation of how it works with more than fifty characters to pass the basic length threshold.",
            hook_and_analogy="This is an explanation of hook and analogy with more than fifty characters to pass the basic length threshold."
        )
        coverage_check = next(r for r in results if r.checkpoint == CheckpointEnum.KEY_POINTS_COVERAGE)
        self.assertFalse(coverage_check.passed)
        self.assertIn("Why it matters", coverage_check.reasoning)

    def test_evaluator_zero_partial_credit_aggregation(self):
        evaluator = ContentEvaluator(llm_client=LLMClient(mock_mode=True))
        bad_draft = LessonDraft(
            topic="RAG",
            iteration=1,
            title="Bad Lesson with Complex Jargon",
            hook_and_analogy="Imagine an open-book exam.",
            what_is_it="This is RAG in simple words.",
            why_it_matters="It helps solve real problems.",
            how_it_works="Step 1 is retrieval.",
            quick_summary_takeaway="Remember this formula.",
            full_content_markdown="This lesson uses high-dimensional vector space and cosine similarity metric."
        )
        report = evaluator.evaluate(bad_draft)
        self.assertFalse(report.overall_passed)
        self.assertIn(CheckpointEnum.NO_UNEXPLAINED_JARGON, report.failed_checkpoints)


if __name__ == "__main__":
    unittest.main()
