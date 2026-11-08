"""Configuration module for the Content Systems Agentic Generator."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# API Keys & Endpoints
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("ANTHROPIC_AUTH_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

OPENROUTER_BASE_URL = os.getenv("ANTHROPIC_BASE_URL", "https://openrouter.ai/api/v1")
if not OPENROUTER_BASE_URL.endswith("/v1") and "openrouter.ai" in OPENROUTER_BASE_URL:
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Selection
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")

# Pipeline Constraints
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
FLESCH_GRADE_CEILING = 8.5  # Max grade level for 12th grade non-native English speaker

# Storage Paths
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_STORE_PATH = MEMORY_DIR / "evolution_store.json"

LOGS_DIR = BASE_DIR / "logs"
REJECTION_LOG_PATH = LOGS_DIR / "rejection_log_summary.json"
RUN_TRACE_LOG_PATH = LOGS_DIR / "pipeline_run_trace.log"

OUTPUT_DOCUMENT_PATH = BASE_DIR / "final_lesson_document.md"

# Target Audience Persona Definition
TARGET_AUDIENCE = {
    "profile": "12th-grade graduate from India",
    "background": "Non-English-medium / regional-medium background, limited English vocabulary",
    "goal": "Wants to kickstart an AI career, understands Hindi/Indian contexts readily",
    "reading_level": "CEFR A2-B1 / Flesch-Kincaid Grade 6 to 8",
    "forbidden_complexity": [
        "latent representations",
        "high-dimensional vector space",
        "cosine similarity metric",
        "stochastic gradient descent",
        "parametric memory vs non-parametric",
        "dense passage retrieval embedding",
        "cross-entropy loss",
        "singular value decomposition"
    ]
}

