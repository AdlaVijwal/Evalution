"""Deterministic, rule-based quality checkpoints for zero-hallucination verification."""

import re
from typing import List, Tuple, Optional
from src.schemas import CheckpointEnum, RubricCheckResult
from src.config import FLESCH_GRADE_CEILING, TARGET_AUDIENCE


def count_syllables(word: str) -> int:
    """Heuristic syllable counter for English words."""
    word = word.lower().strip(".,!?:;\"'()[]{}")
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    # Remove final 'e', 'es', 'ed' if not preceded by vowel
    word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
    word = re.sub(r'^y', '', word)
    vowels = len(re.findall(r'[aeiouy]{1,2}', word))
    return max(1, vowels)


def calculate_readability_metrics(text: str) -> Tuple[float, float, int, int]:
    """Calculate Flesch-Kincaid Grade Level and Flesch Reading Ease."""
    clean_text = re.sub(r'#|\*|-|_', ' ', text)
    sentences = [s.strip() for s in re.split(r'[.!?]+', clean_text) if len(s.strip()) > 3]
    words = [w.strip() for w in re.split(r'\s+', clean_text) if len(w.strip()) > 0]

    num_sentences = max(1, len(sentences))
    num_words = max(1, len(words))
    total_syllables = sum(count_syllables(w) for w in words)

    # Flesch-Kincaid Grade Level = 0.39 * (total words / total sentences) + 11.8 * (total syllables / total words) - 15.59
    fk_grade = 0.39 * (num_words / num_sentences) + 11.8 * (total_syllables / num_words) - 15.59
    fk_grade = max(1.0, round(fk_grade, 2))

    # Flesch Reading Ease = 206.835 - 1.015 * (total words / total sentences) - 84.6 * (total syllables / total words)
    reading_ease = 206.835 - 1.015 * (num_words / num_sentences) - 84.6 * (total_syllables / num_words)
    reading_ease = round(reading_ease, 2)

    return fk_grade, reading_ease, num_sentences, num_words


def check_forbidden_jargon(text: str) -> Tuple[bool, List[str]]:
    """Scan for forbidden high-complexity jargon without immediate simple explanations."""
    flagged = []
    text_lower = text.lower()
    
    # 1. Hard forbidden terms that should never appear for a 12th-grade beginner
    for term in TARGET_AUDIENCE["forbidden_complexity"]:
        if term.lower() in text_lower:
            flagged.append(term)

    # 2. Check for intermediate technical terms that MUST have plain-text explanations
    tech_terms = [
        "vector database",
        "embeddings",
        "hallucination",
        "llm",
        "semantic search"
    ]
    for term in tech_terms:
        if term in text_lower:
            # Check if there is an explanatory phrase within 40 words
            pattern = rf"{term}[\w\s]{{1,150}}(means|like|such as|simple words|think of|imagine|called|stands for)"
            rev_pattern = rf"(means|like|such as|simple words|think of|imagine|called)[\w\s]{{1,150}}{term}"
            if not (re.search(pattern, text_lower) or re.search(rev_pattern, text_lower)):
                flagged.append(f"unexplained '{term}'")

    return (len(flagged) == 0, flagged)


def run_deterministic_evaluations(
    text: str,
    what_is_it: str,
    why_it_matters: str,
    how_it_works: str,
    hook_and_analogy: str
) -> List[RubricCheckResult]:
    """Execute all deterministic, non-LLM checks."""
    results = []

    # 1. Vocabulary & Readability Check
    fk_grade, reading_ease, num_sentences, num_words = calculate_readability_metrics(text)
    avg_words_per_sentence = round(num_words / num_sentences, 1)

    readability_passed = fk_grade <= FLESCH_GRADE_CEILING and avg_words_per_sentence <= 22.0
    reasoning = (
        f"Flesch-Kincaid Grade: {fk_grade} (Ceiling: {FLESCH_GRADE_CEILING}), "
        f"Avg sentence length: {avg_words_per_sentence} words. "
        + ("Comfortably matches 12th-grade Indian beginner level." if readability_passed
           else "Sentences too long or vocabulary too advanced for a 12th-grade beginner.")
    )
    results.append(
        RubricCheckResult(
            checkpoint=CheckpointEnum.BEGINNER_VOCABULARY,
            passed=readability_passed,
            reasoning=reasoning,
            offending_snippet=f"Grade {fk_grade} exceeds limit" if not readability_passed else None,
            prescriptive_action="Shorten long sentences to under 15 words and replace multi-syllable academic words with simpler daily English." if not readability_passed else None
        )
    )

    # 2. Jargon Check
    no_jargon, flagged_terms = check_forbidden_jargon(text)
    jargon_reasoning = (
        "Zero unexplained jargon detected. All technical terms are grounded." if no_jargon
        else f"Detected complex or unexplained jargon: {', '.join(flagged_terms)}"
    )
    results.append(
        RubricCheckResult(
            checkpoint=CheckpointEnum.NO_UNEXPLAINED_JARGON,
            passed=no_jargon,
            reasoning=jargon_reasoning,
            offending_snippet=", ".join(flagged_terms) if not no_jargon else None,
            prescriptive_action="Remove academic terms or immediately add an analogy (e.g., 'like a smart library search') right beside the term." if not no_jargon else None
        )
    )

    # 3. Structural Key Points Coverage (Deterministic check for non-empty required sections)
    sections_present = {
        "What it is": len(what_is_it.strip()) > 50,
        "Why it matters": len(why_it_matters.strip()) > 50,
        "How it works": len(how_it_works.strip()) > 50,
        "Hook & Analogy": len(hook_and_analogy.strip()) > 50,
    }
    missing_sections = [sec for sec, present in sections_present.items() if not present]
    coverage_passed = len(missing_sections) == 0
    coverage_reasoning = (
        "All 4 mandatory educational sections are thoroughly covered." if coverage_passed
        else f"Missing or incomplete required sections: {', '.join(missing_sections)}"
    )
    results.append(
        RubricCheckResult(
            checkpoint=CheckpointEnum.KEY_POINTS_COVERAGE,
            passed=coverage_passed,
            reasoning=coverage_reasoning,
            offending_snippet=f"Missing {', '.join(missing_sections)}" if not coverage_passed else None,
            prescriptive_action="Ensure 'What it is', 'Why it matters', and 'How it works' each have at least 2 detailed paragraphs." if not coverage_passed else None
        )
    )

    return results

