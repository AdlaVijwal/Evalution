"""Streamlit Web UI Dashboard for the Self-Evaluating Lesson Content Generator."""

import json
from pathlib import Path
import streamlit as st

from src.utils.llm_client import LLMClient
from src.generator.generator import LessonGenerator
from src.evaluator.evaluator import ContentEvaluator
from src.memory.evolution_manager import EvolutionMemoryManager
from src.graph.workflow import ContentGraphOrchestrator
from src.config import MEMORY_STORE_PATH, REJECTION_LOG_PATH, OUTPUT_DOCUMENT_PATH

st.set_page_config(
    page_title="Self-Evaluating Lesson Content Generator",
    page_icon="🎓",
    layout="wide"
)

# Header
st.title("🎓 Self-Evaluating Lesson Content Generator")
st.caption(
    "**Role:** GenAI Engineer – Content Systems | "
    "**Target Audience:** 12th-grade graduate from India (Regional-medium, zero AI background)"
)

# Sidebar
st.sidebar.header("⚙️ Pipeline Configuration")
topic = st.sidebar.text_input("Lesson Topic", value="Introduction to RAG")
max_retries = st.sidebar.slider("Max Retries (Termination Bound)", min_value=1, max_value=3, value=2)

deliberate_error = st.sidebar.selectbox(
    "🧪 Inject Deliberate Error (Loom Demo)",
    options=["None", "PHD_JARGON", "MISSING_ANALOGY", "INCOMPLETE_STRUCTURE"],
    index=0,
    help="Deliberately injects a pedagogical or technical flaw to test if the evaluator catches it."
)
error_type = None if deliberate_error == "None" else deliberate_error

offline_mode = st.sidebar.checkbox("Offline / Mock Mode", value=False)

st.sidebar.divider()
st.sidebar.subheader("🧠 Self-Evolving Memory")
memory_manager = EvolutionMemoryManager()
memory_data = memory_manager.load_data()
st.sidebar.metric("Total Pipeline Runs", memory_data.get("total_runs_recorded", 0))

with st.sidebar.expander("Active Learned Guardrails"):
    for rule in memory_data.get("learned_guardrails", []):
        st.markdown(f"⚡ *{rule}*")

with st.sidebar.expander("Historical Failure Tally"):
    st.json(memory_data.get("historical_failure_counts", {}))

# Main Execution Trigger
if st.button("🚀 Run Agentic Pipeline", type="primary", use_container_width=True):
    llm_client = LLMClient(mock_mode=offline_mode)
    generator = LessonGenerator(llm_client=llm_client)
    evaluator = ContentEvaluator(llm_client=llm_client)

    orchestrator = ContentGraphOrchestrator(
        generator=generator,
        evaluator=evaluator,
        memory_manager=memory_manager
    )

    with st.spinner("Executing autonomous Generate ➔ Evaluate ➔ Regenerate loop..."):
        result_state = orchestrator.run(
            topic=topic,
            max_retries=max_retries,
            deliberate_error_type=error_type
        )

    # Success / Failure Banner
    if result_state["is_final_approved"]:
        st.success(
            f"🎉 Content Approved! Successfully passed all 6 checkpoints on Iteration {result_state['iteration']}."
        )
    else:
        st.error(
            f"⚠️ Reached maximum retry limit ({max_retries}) without full approval. Pipeline halted safely."
        )

    # Tabs for Each Iteration Draft
    drafts = result_state.get("draft_history", [])
    reports = result_state.get("evaluation_reports", [])

    if drafts:
        tab_labels = [f"Draft Iteration #{d.iteration}" for d in drafts]
        tabs = st.tabs(tab_labels)

        for i, tab in enumerate(tabs):
            draft = drafts[i]
            report = reports[i] if i < len(reports) else None

            with tab:
                col_left, col_right = st.columns([1.2, 1])

                with col_left:
                    st.subheader(f"📝 {draft.title}")
                    st.markdown(draft.full_content_markdown)

                with col_right:
                    st.subheader("⚖️ Rubric Evaluation Scorecard")
                    if report:
                        st.markdown(
                            f"**Overall Verdict:** "
                            f"{'🟢 PASSED ALL' if report.overall_passed else '🔴 REJECTED'}"
                        )
                        for check in report.checks:
                            badge = "✅ PASS" if check.passed else "❌ FAIL"
                            with st.expander(f"{badge} : {check.checkpoint.value}", expanded=not check.passed):
                                st.write(f"**Reasoning:** {check.reasoning}")
                                if check.offending_snippet:
                                    st.warning(f"**Offending Snippet:** \"{check.offending_snippet}\"")
                                if check.prescriptive_action:
                                    st.info(f"**Prescribed Fix:** {check.prescriptive_action}")

    # Rejection Log Section
    st.divider()
    st.subheader("📋 Rejection Log & Diagnostic Trace")
    rejection_entries = result_state.get("rejection_log", [])
    if rejection_entries:
        for entry in rejection_entries:
            with st.container(border=True):
                st.markdown(f"#### 🚫 Iteration #{entry.iteration} Rejected")
                st.markdown(f"**Failed Checkpoints:** `{', '.join(entry.failed_checks)}`")
                st.markdown("**Why it failed:**")
                for r in entry.why_it_failed:
                    st.markdown(f"- {r}")
                st.markdown(f"**Action Prescribed on Retry:** {entry.what_was_changed_on_retry}")
    else:
        st.info("No rejections recorded. Draft passed on attempt #1!")

else:
    # Display previously saved deliverables if available
    st.info("Click 'Run Agentic Pipeline' above to execute the live agentic loop.")

    col1, col2 = st.columns(2)
    with col1:
        if OUTPUT_DOCUMENT_PATH.exists():
            st.subheader("📄 Current Approved Lesson (Ship Gate)")
            with open(OUTPUT_DOCUMENT_PATH, "r", encoding="utf-8") as f:
                st.markdown(f.read())

    with col2:
        if REJECTION_LOG_PATH.exists():
            st.subheader("📋 Most Recent Rejection Log Summary")
            with open(REJECTION_LOG_PATH, "r", encoding="utf-8") as f:
                st.json(json.load(f))

