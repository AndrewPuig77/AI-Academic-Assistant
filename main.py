"""
Academic AI Assistant - Main Streamlit Application
A powerful tool for analyzing research papers and class materials with Google Gemini (default),
OpenAI, Anthropic Claude, or any OpenAI-compatible model
Supporting both research analysis and student study tools
"""

import streamlit as st
import html
import os
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.core.document_processor import DocumentProcessor
from app.core.gemini_analyzer import GeminiAnalyzer
from app.core.providers import PROVIDERS, get_builtin_key
from app.utils.helpers import format_analysis_results, create_download_link
from app.utils.report_generator import AdvancedReportGenerator

# Page configuration
st.set_page_config(
    page_title="Academic AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Global styles
st.markdown("""
<style>
    :root {
        --bg: #0b0f17;
        --surface: #111827;
        --surface-2: #161f2e;
        --border: #1f2937;
        --border-strong: #2b3646;
        --text: #e5e7eb;
        --muted: #9ca3af;
        --accent: #6366f1;
        --accent-soft: rgba(99, 102, 241, 0.12);
        --accent-text: #a5b4fc;
        --radius: 12px;
    }

    .stApp { background: var(--bg); }

    /* Streamlit chrome */
    #MainMenu, footer, .stDeployButton, [data-testid="stAppDeployButton"], [data-testid="stDecoration"] { display: none !important; }
    [data-testid="stHeader"] { background: transparent; }

    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 4rem;
        max-width: 1200px;
    }

    h1, h2, h3, h4 { letter-spacing: -0.02em; color: var(--text); }

    /* Hero */
    .hero {
        padding: 2rem 2.25rem;
        border: 1px solid var(--border);
        border-radius: 16px;
        background:
            radial-gradient(1200px 300px at 0% 0%, rgba(99, 102, 241, 0.18), transparent 60%),
            var(--surface);
        margin-bottom: 1.75rem;
    }
    .hero-eyebrow {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accent-text);
        background: var(--accent-soft);
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 0.25rem 0.65rem;
        border-radius: 999px;
        margin-bottom: 0.9rem;
    }
    .hero h1 {
        font-size: 2.25rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        padding: 0;
    }
    .hero p {
        color: var(--muted);
        font-size: 1.05rem;
        margin: 0;
        max-width: 720px;
    }

    /* Section headings */
    .section-title { margin: 0.5rem 0 1.25rem 0; }
    .section-title h2 { font-size: 1.4rem; font-weight: 600; margin: 0; padding: 0; }
    .section-title p { color: var(--muted); margin: 0.25rem 0 0 0; font-size: 0.95rem; }

    .label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted);
        margin: 0.25rem 0 0.5rem 0;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        height: 2.75rem;
        padding: 0 1rem;
        color: var(--muted);
        font-weight: 500;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text); }
    .stTabs [aria-selected="true"] { color: var(--text) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: var(--accent); }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 1.75rem; }

    /* Bordered containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: var(--border) !important;
        border-radius: var(--radius) !important;
        background: var(--surface);
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 500;
        border: 1px solid var(--border-strong);
        background: var(--surface-2);
        color: var(--text);
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--accent);
        color: var(--text);
        background: var(--accent-soft);
    }
    .stButton > button[kind="primary"] {
        background: var(--accent);
        border-color: var(--accent);
        color: #ffffff;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background: #4f46e5;
        border-color: #4f46e5;
    }
    .stButton > button:disabled, .stButton > button[kind="primary"]:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }

    /* File uploader */
    [data-testid="stFileUploaderDropzone"] {
        background: var(--surface-2);
        border: 1.5px dashed var(--border-strong);
        border-radius: var(--radius);
    }
    [data-testid="stFileUploaderDropzone"]:hover { border-color: var(--accent); }

    /* Expanders */
    [data-testid="stExpander"] details {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--surface);
    }
    [data-testid="stExpander"] summary { font-weight: 500; }

    /* Metric cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.75rem;
        margin-bottom: 1.5rem;
    }
    .metric {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--surface);
        padding: 1rem 1.1rem;
        min-width: 0;
    }
    .metric .k {
        font-size: 0.75rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 600;
    }
    .metric .v {
        font-size: 1.15rem;
        font-weight: 600;
        color: var(--text);
        margin-top: 0.3rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Feature cards */
    .card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 0.9rem;
        margin: 0.5rem 0 1.5rem 0;
    }
    .card {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--surface);
        padding: 1.15rem 1.2rem;
        transition: border-color 0.15s ease;
    }
    .card:hover { border-color: var(--border-strong); }
    .card .icon {
        width: 2.1rem;
        height: 2.1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 8px;
        background: var(--accent-soft);
        font-size: 1.05rem;
        margin-bottom: 0.75rem;
    }
    .card h4 { font-size: 0.98rem; font-weight: 600; margin: 0 0 0.3rem 0; padding: 0; }
    .card p { font-size: 0.88rem; color: var(--muted); margin: 0; line-height: 1.5; }

    /* Empty state */
    .empty {
        border: 1px dashed var(--border-strong);
        border-radius: var(--radius);
        padding: 1.5rem;
        text-align: center;
        color: var(--muted);
        margin-bottom: 1.5rem;
    }
    .empty strong { color: var(--text); display: block; margin-bottom: 0.25rem; font-size: 1rem; }

    /* Flashcards */
    .flashcard {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        background: var(--surface-2);
        padding: 1rem 1.1rem;
        height: 100%;
    }
    .flashcard .side {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--accent-text);
        margin-bottom: 0.4rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
    }
    .brand { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.25rem; }
    .brand .logo {
        width: 2rem; height: 2rem; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        background: var(--accent); font-size: 1rem;
    }
    .brand .name { font-weight: 700; font-size: 1.05rem; color: var(--text); }
    .steps { list-style: none; padding: 0; margin: 0; }
    .steps li {
        display: flex; gap: 0.7rem; align-items: flex-start;
        padding: 0.45rem 0; color: var(--muted); font-size: 0.9rem;
    }
    .steps .n {
        flex: none; width: 1.4rem; height: 1.4rem; border-radius: 999px;
        border: 1px solid var(--border-strong); color: var(--text);
        font-size: 0.75rem; font-weight: 600;
        display: flex; align-items: center; justify-content: center;
    }
    .status-pill {
        display: inline-flex; align-items: center; gap: 0.4rem;
        font-size: 0.8rem; color: var(--muted);
    }
    .status-pill .dot { width: 0.5rem; height: 0.5rem; border-radius: 999px; background: #4b5563; }
    .status-pill.ok .dot { background: #22c55e; }
    .status-pill.ready .dot { background: #f59e0b; }
    .sidebar-foot { color: var(--muted); font-size: 0.8rem; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


def type_label(document_type: str) -> str:
    """Strip the leading emoji from a document type for display."""
    return document_type.split(" ", 1)[-1]


def section_title(title: str, subtitle: str = ""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="section-title"><h2>{title}</h2>{sub}</div>', unsafe_allow_html=True)


def label(text: str):
    st.markdown(f'<div class="label">{text}</div>', unsafe_allow_html=True)


def card_grid(cards):
    """Render (icon, title, description) tuples as a responsive card grid."""
    markup = "".join(
        f'<div class="card"><div class="icon">{icon}</div><h4>{title}</h4><p>{desc}</p></div>'
        for icon, title, desc in cards
    )
    st.markdown(f'<div class="card-grid">{markup}</div>', unsafe_allow_html=True)


def empty_state(title: str, message: str):
    st.markdown(f'<div class="empty"><strong>{title}</strong>{message}</div>', unsafe_allow_html=True)


def metric_grid(items):
    markup = "".join(
        f'<div class="metric"><div class="k">{k}</div><div class="v" title="{v}">{v}</div></div>'
        for k, v in ((k, html.escape(v)) for k, v in items)
    )
    st.markdown(f'<div class="metric-grid">{markup}</div>', unsafe_allow_html=True)


def file_stem(name: str) -> str:
    return Path(name).stem


RESEARCH_TOOLS = [
    ("🔍", "Related Papers", "Find similar research, search strategies, and cross-disciplinary connections."),
    ("❓", "Research Questions", "Generate meaningful questions and methodological improvements for future work."),
    ("💡", "Hypothesis Builder", "Develop testable hypotheses, novel applications, and alternative explanations."),
    ("📋", "Proposal Assistant", "Draft a structured research proposal aligned with grant requirements."),
]

STUDY_TOOLS = [
    ("📇", "Flashcards", "Key definitions and concepts formatted for active recall."),
    ("❓", "Practice Questions", "Multiple-choice, short-answer, and essay questions."),
    ("📖", "Study Guide", "Topic-organized summaries and quick review checklists."),
    ("📊", "Material Analysis", "Difficulty assessment, study recommendations, and exam focus."),
]


def provider_short_name(provider: str) -> str:
    return PROVIDERS[provider]["label"].split(" (")[0]


def render_provider_settings() -> dict:
    """Sidebar controls for choosing the AI provider, model, and (optionally) the user's own key."""
    label("AI provider")
    provider = st.selectbox(
        "AI provider",
        list(PROVIDERS),
        format_func=lambda p: PROVIDERS[p]["label"],
        key="llm_provider",
        label_visibility="collapsed",
        help="Google Gemini is the default. OpenAI-compatible covers Groq, OpenRouter, Together, "
             "and local servers like Ollama or LM Studio.",
    )
    info = PROVIDERS[provider]
    builtin_key = get_builtin_key(provider)
    is_compatible = provider == "openai_compatible"

    base_url = ""
    if is_compatible:
        base_url = st.text_input(
            "Base URL",
            key="llm_base_url",
            placeholder="https://api.groq.com/openai/v1",
            help="Groq: https://api.groq.com/openai/v1 · OpenRouter: https://openrouter.ai/api/v1 · "
                 "Ollama (local): http://localhost:11434/v1",
        ).strip()

    model = st.text_input(
        "Model",
        key=f"llm_model_{provider}",
        placeholder=info["default_model"] or "e.g. llama-3.3-70b-versatile",
        help="Leave blank to use the default shown." if info["default_model"] else "The model name on your server.",
    ).strip()

    api_key = st.text_input(
        "API key",
        type="password",
        key=f"llm_key_{provider}",
        placeholder="Using the app's built-in key" if builtin_key else ("Optional for local servers" if is_compatible else "Paste your API key"),
        help="Your key is only kept for this browser session and is never saved.",
    ).strip()

    if is_compatible:
        ready = bool(base_url and model)
        hint = "Using your key for this session." if api_key else "Enter a base URL and model to get started."
    else:
        ready = bool(api_key or builtin_key)
        if api_key:
            hint = "Using your key for this session."
        elif builtin_key:
            hint = "Using the app's built-in key."
        else:
            hint = f"Add your {info['label']} API key to run analyses."
    if ready:
        st.caption(hint)
    else:
        st.warning(hint, icon=":material/key:")
    if info["key_url"] and not builtin_key and not api_key:
        st.markdown(f'<div class="sidebar-foot"><a href="{info["key_url"]}" target="_blank">Get a {info["label"]} key →</a></div>',
                    unsafe_allow_html=True)

    return {
        "provider": provider,
        "api_key": api_key or None,
        "model": model or None,
        "base_url": base_url or None,
        "ready": ready,
        "name": provider_short_name(provider),
    }


def make_analyzer(ai: dict) -> GeminiAnalyzer:
    return GeminiAnalyzer(provider=ai["provider"], api_key=ai["api_key"], model_name=ai["model"], base_url=ai["base_url"])


def render_sidebar() -> tuple:
    """Render the sidebar. Returns the AI settings and a slot for the document status,
    which is filled after the tabs so it reflects this run's upload/analysis."""
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="logo">🎓</div><div class="name">Academic AI Assistant</div></div>',
            unsafe_allow_html=True
        )
        status_slot = st.container()

        st.divider()
        ai = render_provider_settings()

        st.divider()
        label("How it works")
        st.markdown("""
        <ul class="steps">
            <li><span class="n">1</span>Choose a document type and upload a PDF, DOCX, or TXT file.</li>
            <li><span class="n">2</span>Select the analyses you need and run them.</li>
            <li><span class="n">3</span>Review results, then use Research or Study tools.</li>
            <li><span class="n">4</span>Export reports and study materials.</li>
        </ul>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown(
            '<div class="sidebar-foot">Selecting the right document type tailors the analysis to your material.</div>',
            unsafe_allow_html=True
        )

    return ai, status_slot


def render_document_status(status_slot, uploaded_file, has_document: bool):
    analyzed_name = st.session_state.get('paper_name', '')

    if uploaded_file is not None and (not has_document or uploaded_file.name != analyzed_name):
        status_class, status_text, caption = "ready", "Ready to analyze", uploaded_file.name
    elif has_document:
        status_class, status_text, caption = "ok", "Document analyzed", analyzed_name
    else:
        status_class, status_text, caption = "", "No document loaded", ""

    with status_slot:
        st.markdown(
            f'<div class="status-pill {status_class}"><span class="dot"></span>{status_text}</div>',
            unsafe_allow_html=True
        )
        if caption:
            st.caption(caption)


# Session keys produced by tools for a specific document; cleared when a new document is analyzed
DOCUMENT_OUTPUT_KEYS = [
    'related_papers', 'research_questions', 'hypotheses', 'research_proposal',
    'study_flashcards', 'study_questions', 'study_guide', 'material_analysis', 'show_report',
]


def main():
    has_document = bool(st.session_state.get('analyzed_content') and st.session_state.get('analysis_results'))

    if st.session_state.pop('analysis_just_completed', False):
        st.toast("Analysis complete — open the Results tab", icon=":material/check_circle:")

    ai, status_slot = render_sidebar()

    # Hero
    st.markdown(f"""
    <div class="hero">
        <div class="hero-eyebrow">Powered by {html.escape(ai["name"])}</div>
        <h1>Academic AI Assistant</h1>
        <p>Turn research papers and course materials into structured analysis, research directions,
        and ready-to-use study resources.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Upload & Analyze", "Results", "Research Tools", "Study Tools", "About"])


    with tab1:
        section_title("Upload a document", "Supported formats: PDF, DOCX, and TXT up to 10 MB.")

        left, right = st.columns([1, 1], gap="large")

        with left:
            label("Document type")
            document_type = st.selectbox(
                "What type of document are you analyzing?",
                [
                    "🔬 Research Paper",
                    "📚 Textbook Chapter",
                    "📝 Lecture Notes",
                    "📋 Assignment/Homework",
                    "📄 Article/Essay",
                    "📊 Report/Thesis",
                    "🎓 Study Guide",
                    "🗒️ Class Handout",
                    "📖 Other Academic Material"
                ],
                format_func=type_label,
                label_visibility="collapsed",
                help="Select the type of document to get the most relevant analysis options"
            )

            label("File")
            uploaded_file = st.file_uploader(
                "Choose your document",
                type=['pdf', 'docx', 'txt'],
                label_visibility="collapsed",
                help="Upload a research paper, textbook chapter, lecture notes, or any academic material (PDF, Word, or Text format - max 10MB)"
            )

            if uploaded_file is not None:
                metric_grid([
                    ("File", uploaded_file.name),
                    ("Size", f"{uploaded_file.size / 1024 / 1024:.2f} MB"),
                ])

        with right:
            if uploaded_file is None:
                empty_state("No file selected", "Upload a document to configure analysis options.")
            else:
                with st.container(border=True):
                    label("Core analysis")
                    include_summary = st.checkbox("Summary", value=True)
                    include_keywords = st.checkbox("Keywords & key terms", value=True)
                    detailed_analysis = st.checkbox("Detailed analysis", value=False)

                    # Document-specific options
                    if document_type == "🔬 Research Paper":
                        label("Research paper")
                        col1, col2 = st.columns(2)
                        with col1:
                            include_methodology = st.checkbox("Methodology", value=True)
                            include_citations = st.checkbox("Citations", value=True)
                        with col2:
                            include_gaps = st.checkbox("Research gaps", value=True)
                            include_future_work = st.checkbox("Future directions", value=False)

                    elif document_type in ["📚 Textbook Chapter", "📝 Lecture Notes", "🗒️ Class Handout"]:
                        label("Study material")
                        col1, col2 = st.columns(2)
                        with col1:
                            include_concepts = st.checkbox("Key concepts", value=True)
                            include_examples = st.checkbox("Examples & cases", value=True)
                        with col2:
                            include_questions = st.checkbox("Study questions", value=True)
                            include_difficulty = st.checkbox("Difficulty level", value=False)

                        # Set research-specific options to False for study materials
                        include_methodology = False
                        include_citations = False
                        include_gaps = False
                        include_future_work = False

                    elif document_type in ["📋 Assignment/Homework", "📄 Article/Essay"]:
                        label("Assignment / essay")
                        col1, col2 = st.columns(2)
                        with col1:
                            include_structure = st.checkbox("Structure", value=True)
                            include_arguments = st.checkbox("Key arguments", value=True)
                        with col2:
                            include_improvements = st.checkbox("Improvement suggestions", value=False)
                            include_sources = st.checkbox("Source analysis", value=True)

                        # Set research-specific options conditionally
                        include_methodology = False
                        include_citations = include_sources  # Map to source analysis
                        include_gaps = False
                        include_future_work = False

                    elif document_type in ["📊 Report/Thesis", "🎓 Study Guide"]:
                        label("Report / guide")
                        col1, col2 = st.columns(2)
                        with col1:
                            include_structure = st.checkbox("Structure", value=True)
                            include_findings = st.checkbox("Key findings", value=True)
                        with col2:
                            include_recommendations = st.checkbox("Recommendations", value=True)
                            include_citations = st.checkbox("References", value=True)

                        # Partial research features
                        include_methodology = st.checkbox("Approach / methods", value=False) if document_type == "📊 Report/Thesis" else False
                        include_gaps = False
                        include_future_work = False

                    else:  # Other Academic Material
                        label("General")
                        col1, col2 = st.columns(2)
                        with col1:
                            include_structure = st.checkbox("Structure", value=True)
                            include_main_points = st.checkbox("Main points", value=True)
                        with col2:
                            include_context = st.checkbox("Context", value=False)
                            include_citations = st.checkbox("References", value=False)

                        # Minimal research features
                        include_methodology = False
                        include_gaps = False
                        include_future_work = False

                analyze_clicked = st.button(
                    f"Analyze {type_label(document_type).split('/')[0].lower()}",
                    type="primary",
                    icon=":material/auto_awesome:",
                    use_container_width=True,
                    disabled=not ai["ready"]
                )
                if not ai["ready"]:
                    st.caption("Set up an AI provider in the sidebar to run the analysis.")

                if analyze_clicked:
                    analysis_succeeded = False
                    with st.status("Analyzing document…", expanded=True) as status:
                        try:
                            st.write("Initializing AI processors")
                            document_processor = DocumentProcessor()
                            analyzer = make_analyzer(ai)

                            st.write("Saving uploaded file")
                            temp_path = f"uploads/{uploaded_file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(uploaded_file.read())

                            st.write("Extracting text")
                            extracted_text = document_processor.extract_text(temp_path)

                            analysis_options = {
                                'document_type': document_type,
                                'summary': include_summary,
                                'methodology': include_methodology if 'include_methodology' in locals() else False,
                                'citations': include_citations if 'include_citations' in locals() else False,
                                'gaps': include_gaps if 'include_gaps' in locals() else False,
                                'keywords': include_keywords,
                                'detailed': detailed_analysis,
                                'concepts': include_concepts if 'include_concepts' in locals() else False,
                                'examples': include_examples if 'include_examples' in locals() else False,
                                'questions': include_questions if 'include_questions' in locals() else False,
                                'difficulty': include_difficulty if 'include_difficulty' in locals() else False,
                                'structure': include_structure if 'include_structure' in locals() else False,
                                'arguments': include_arguments if 'include_arguments' in locals() else False,
                                'improvements': include_improvements if 'include_improvements' in locals() else False,
                                'findings': include_findings if 'include_findings' in locals() else False,
                                'recommendations': include_recommendations if 'include_recommendations' in locals() else False,
                                'main_points': include_main_points if 'include_main_points' in locals() else False,
                                'context': include_context if 'include_context' in locals() else False,
                                'future_work': include_future_work if 'include_future_work' in locals() else False
                            }

                            st.write(f"Analyzing with {ai['name']} — this may take a moment")
                            analysis_results = analyzer.analyze_paper(extracted_text, analysis_options)

                            for key in DOCUMENT_OUTPUT_KEYS:
                                st.session_state.pop(key, None)
                            st.session_state['analysis_results'] = analysis_results
                            st.session_state['analyzed_content'] = extracted_text
                            st.session_state['paper_name'] = uploaded_file.name

                            os.remove(temp_path)
                            status.update(label="Analysis complete — open the Results tab", state="complete", expanded=False)
                            analysis_succeeded = True

                        except Exception as e:
                            status.update(label="Analysis failed", state="error", expanded=True)
                            st.error(f"Error during analysis: {str(e)}")

                    # Rerun so the sidebar and the other tabs pick up the new document
                    if analysis_succeeded:
                        st.session_state['analysis_just_completed'] = True
                        st.rerun()

    with tab2:
        if 'analysis_results' in st.session_state:
            results = st.session_state['analysis_results']
            document_name = st.session_state.get('paper_name', 'Unknown Document')
            document_type = results.get('document_type', 'Unknown Type')
            is_research = "Research Paper" in document_type

            result_sections = [
                ('summary', "Paper summary" if is_research else "Summary", ":material/summarize:"),
                ('methodology', "Methodology", ":material/science:"),
                ('gaps', "Research gaps", ":material/travel_explore:"),
                ('future_work', "Future research directions", ":material/trending_up:"),
                ('concepts', "Key concepts", ":material/lightbulb:"),
                ('examples', "Examples & cases", ":material/cases:"),
                ('questions', "Study questions", ":material/quiz:"),
                ('difficulty', "Difficulty assessment", ":material/speed:"),
                ('structure', "Structure", ":material/account_tree:"),
                ('arguments', "Key arguments", ":material/forum:"),
                ('improvements', "Improvement suggestions", ":material/edit_note:"),
                ('findings', "Key findings", ":material/insights:"),
                ('recommendations', "Recommendations", ":material/recommend:"),
                ('main_points', "Main points", ":material/format_list_bulleted:"),
                ('context', "Context", ":material/public:"),
                ('citations', "Citations & references" if is_research else "References & sources", ":material/menu_book:"),
                ('keywords', "Key terms & concepts", ":material/sell:"),
                ('detailed', "Detailed analysis", ":material/description:"),
            ]
            available = [s for s in result_sections if results.get(s[0])]
            word_count = len(st.session_state.get('analyzed_content', '').split())

            section_title("Analysis results", document_name)
            metric_grid([
                ("Document type", type_label(document_type)),
                ("Sections", str(len(available))),
                ("Words analyzed", f"{word_count:,}"),
            ])

            for i, (key, title, icon) in enumerate(available):
                with st.expander(title, expanded=(i == 0), icon=icon):
                    st.markdown(results[key])

            st.divider()
            label("Export")
            col1, col2, _ = st.columns([1, 1, 2])
            with col1:
                st.download_button(
                    label="Download as text",
                    data=format_analysis_results(results, document_name),
                    file_name=f"analysis_{file_stem(document_name)}.txt",
                    mime='text/plain',
                    icon=":material/download:",
                    use_container_width=True
                )
            with col2:
                if st.session_state.get('show_report'):
                    if st.button("Hide full report", icon=":material/visibility_off:", use_container_width=True):
                        st.session_state['show_report'] = False
                        st.rerun()
                elif st.button("Generate full report", icon=":material/analytics:", use_container_width=True):
                    st.session_state['show_report'] = True
                    st.rerun()

            # Kept in session state so the report survives the rerun triggered by its download buttons
            if st.session_state.get('show_report'):
                report_generator = AdvancedReportGenerator()
                report_generator.display_streamlit_report(results, document_name)

        else:
            section_title("Analysis results")
            empty_state("No results yet", "Upload and analyze a document in the Upload & Analyze tab.")

    with tab3:
        section_title("Research tools", "Generate research directions from your analyzed paper.")

        if has_document:
            tools = [
                ('related_papers', "Find related papers", ":material/travel_explore:", "Analyzing research landscape…",
                 lambda a, c: a.suggest_related_papers(c), "Related papers & research areas", "related_papers_guide.txt"),
                ('research_questions', "Generate research questions", ":material/help:", "Generating research questions…",
                 lambda a, c: a.generate_research_questions(c), "Research questions", "research_questions.txt"),
                ('hypotheses', "Build hypotheses", ":material/lightbulb:", "Building hypotheses…",
                 lambda a, c: a.build_hypotheses(c), "Hypotheses", "research_hypotheses.txt"),
                ('research_proposal', "Draft research proposal", ":material/description:", "Drafting research proposal…",
                 lambda a, c: a.generate_research_proposal(c), "Research proposal draft", "research_proposal_draft.txt"),
            ]

            cols = st.columns(4)
            for col, (key, button_label, icon, spinner_text, run, _, _) in zip(cols, tools):
                with col:
                    if st.button(button_label, icon=icon, use_container_width=True, key=f"btn_{key}", disabled=not ai["ready"]):
                        with st.spinner(spinner_text):
                            try:
                                st.session_state[key] = run(make_analyzer(ai), st.session_state.analyzed_content)
                            except Exception as e:
                                st.error(str(e))

            generated = [t for t in tools if t[0] in st.session_state]
            if generated:
                st.write("")
                for key, _, icon, _, _, title, file_name in generated:
                    with st.expander(title, expanded=True, icon=icon):
                        st.markdown(st.session_state[key])
                        st.download_button(
                            label="Download",
                            data=st.session_state[key],
                            file_name=file_name,
                            mime="text/plain",
                            icon=":material/download:",
                            key=f"dl_{key}"
                        )
        else:
            empty_state("No document analyzed", "Analyze a document first to unlock research tools.")
            card_grid(RESEARCH_TOOLS)

    with tab4:
        section_title("Study tools", "Create study resources from your class material.")

        if not has_document:
            empty_state("No material analyzed", "Analyze class material first to unlock study tools.")
            card_grid(STUDY_TOOLS)
        else:
            material_name = st.session_state.get('paper_name', 'Class Material')
            analyzed_content = st.session_state.get('analyzed_content', '')
            material_stem = file_stem(material_name)

            with st.container(border=True):
                label("Options")
                opt1, opt2, opt3 = st.columns(3)
                with opt1:
                    question_types = st.multiselect(
                        "Question types",
                        ["multiple_choice", "short_answer", "essay"],
                        default=["multiple_choice", "short_answer"],
                        format_func=lambda q: q.replace("_", " ").capitalize(),
                        key="question_types_selector"
                    )
                with opt2:
                    topic_name = st.text_input(
                        "Study guide topic",
                        value=material_stem,
                        key="study_guide_topic"
                    ) or material_name
                with opt3:
                    material_type = st.selectbox(
                        "Material type",
                        ["textbook", "lecture_notes", "assignment", "handout", "other"],
                        format_func=lambda m: m.replace("_", " ").capitalize(),
                        key="material_type_selector"
                    )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("Flashcards", icon=":material/style:", use_container_width=True, disabled=not ai["ready"]):
                    with st.spinner("Creating flashcards…"):
                        try:
                            st.session_state['study_flashcards'] = make_analyzer(ai).generate_flashcards(analyzed_content)
                        except Exception as e:
                            st.error(f"Error generating flashcards: {str(e)}")

            with col2:
                if st.button("Practice questions", icon=":material/quiz:", use_container_width=True, disabled=not ai["ready"]):
                    if not question_types:
                        st.warning("Select at least one question type.")
                    else:
                        with st.spinner("Creating practice questions…"):
                            try:
                                st.session_state['study_questions'] = make_analyzer(ai).create_practice_questions(
                                    analyzed_content, question_types
                                )
                            except Exception as e:
                                st.error(f"Error creating questions: {str(e)}")

            with col3:
                if st.button("Study guide", icon=":material/menu_book:", use_container_width=True, disabled=not ai["ready"]):
                    with st.spinner("Building study guide…"):
                        try:
                            st.session_state['study_guide'] = make_analyzer(ai).build_study_guide(
                                analyzed_content, topic_name
                            )
                        except Exception as e:
                            st.error(f"Error building study guide: {str(e)}")

            with col4:
                if st.button("Analyze material", icon=":material/analytics:", use_container_width=True, disabled=not ai["ready"]):
                    with st.spinner("Analyzing class material…"):
                        try:
                            st.session_state['material_analysis'] = make_analyzer(ai).analyze_class_material(
                                analyzed_content, material_type
                            )
                        except Exception as e:
                            st.error(f"Error analyzing material: {str(e)}")

            study_keys = ['study_flashcards', 'study_questions', 'study_guide', 'material_analysis']
            if any(key in st.session_state for key in study_keys):
                st.write("")

            # Flashcards Display
            flashcards = None
            if 'study_flashcards' in st.session_state:
                flashcards_text = st.session_state['study_flashcards']
                try:
                    # Extract JSON from response
                    json_match = re.search(r'\[(.*?)\]', flashcards_text, re.DOTALL)
                    if json_match:
                        flashcards = json.loads('[' + json_match.group(1) + ']')
                except Exception:
                    flashcards = None

                title = f"Flashcards ({len(flashcards)})" if flashcards else "Flashcards"
                with st.expander(title, icon=":material/style:"):
                    if flashcards:
                        for i, card in enumerate(flashcards, 1):
                            front_col, back_col = st.columns(2)
                            with front_col:
                                st.markdown(
                                    f'<div class="flashcard"><div class="side">Card {i} · Front</div>{html.escape(str(card.get("front", "")))}</div>',
                                    unsafe_allow_html=True
                                )
                            with back_col:
                                st.markdown(
                                    f'<div class="flashcard"><div class="side">Back</div>{html.escape(str(card.get("back", "")))}</div>',
                                    unsafe_allow_html=True
                                )
                            st.write("")
                    else:
                        st.markdown(flashcards_text)

            if 'study_questions' in st.session_state:
                with st.expander("Practice questions", icon=":material/quiz:"):
                    st.markdown(st.session_state['study_questions'])

            if 'study_guide' in st.session_state:
                with st.expander("Study guide", icon=":material/menu_book:"):
                    st.markdown(st.session_state['study_guide'])

            if 'material_analysis' in st.session_state:
                with st.expander("Material analysis", icon=":material/analytics:"):
                    analysis_data = st.session_state['material_analysis']
                    if isinstance(analysis_data, dict):
                        metric_grid([
                            ("Material type", str(analysis_data.get('material_type', 'Unknown')).replace("_", " ").capitalize()),
                            ("Content length", f"{analysis_data.get('content_length', 0):,} chars"),
                        ])
                        st.markdown(analysis_data.get('analysis', 'No analysis available'))
                    else:
                        st.markdown(analysis_data)

            # Export Section
            if any(key in st.session_state for key in study_keys):
                st.divider()
                label("Export")
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                export_col1, export_col2, export_col3, export_col4 = st.columns(4)

                with export_col1:
                    if 'study_flashcards' in st.session_state:
                        if flashcards:
                            flashcards_export = f"FLASHCARDS - {material_name}\nGenerated: {timestamp}\n\n"
                            for i, card in enumerate(flashcards, 1):
                                flashcards_export += f"CARD {i}\nFront: {card.get('front', '')}\nBack: {card.get('back', '')}\n\n"
                        else:
                            flashcards_export = st.session_state['study_flashcards']
                        st.download_button(
                            label="Flashcards",
                            data=flashcards_export,
                            file_name=f"flashcards_{material_stem}.txt",
                            mime="text/plain",
                            icon=":material/download:",
                            use_container_width=True
                        )

                with export_col2:
                    if 'study_questions' in st.session_state:
                        st.download_button(
                            label="Questions",
                            data=f"PRACTICE QUESTIONS - {material_name}\nGenerated: {timestamp}\n\n{st.session_state['study_questions']}",
                            file_name=f"questions_{material_stem}.txt",
                            mime="text/plain",
                            icon=":material/download:",
                            use_container_width=True
                        )

                with export_col3:
                    if 'study_guide' in st.session_state:
                        st.download_button(
                            label="Study guide",
                            data=f"STUDY GUIDE - {material_name}\nGenerated: {timestamp}\n\n{st.session_state['study_guide']}",
                            file_name=f"study_guide_{material_stem}.txt",
                            mime="text/plain",
                            icon=":material/download:",
                            use_container_width=True
                        )

                with export_col4:
                    combined_content = f"COMPLETE STUDY PACKAGE - {material_name}\n"
                    combined_content += f"Generated: {timestamp}\n"
                    combined_content += "=" * 60 + "\n\n"

                    if 'study_flashcards' in st.session_state:
                        combined_content += "FLASHCARDS\n" + "=" * 20 + "\n"
                        combined_content += st.session_state['study_flashcards'] + "\n\n"

                    if 'study_questions' in st.session_state:
                        combined_content += "PRACTICE QUESTIONS\n" + "=" * 20 + "\n"
                        combined_content += st.session_state['study_questions'] + "\n\n"

                    if 'study_guide' in st.session_state:
                        combined_content += "STUDY GUIDE\n" + "=" * 20 + "\n"
                        combined_content += st.session_state['study_guide'] + "\n\n"

                    if 'material_analysis' in st.session_state:
                        combined_content += "MATERIAL ANALYSIS\n" + "=" * 20 + "\n"
                        analysis_data = st.session_state['material_analysis']
                        if isinstance(analysis_data, dict):
                            combined_content += analysis_data.get('analysis', 'No analysis available')
                        else:
                            combined_content += str(analysis_data)

                    st.download_button(
                        label="All materials",
                        data=combined_content,
                        file_name=f"study_package_{material_stem}.txt",
                        mime="text/plain",
                        icon=":material/inventory_2:",
                        type="primary",
                        use_container_width=True
                    )

    with tab5:
        section_title(
            "About",
            "An AI assistant that helps researchers, students, and educators understand complex documents "
            "and turn them into effective study materials."
        )

        label("Research analysis")
        card_grid([
            ("📄", "Document Processing", "Text extraction from PDF, DOCX, and TXT with structure preservation."),
            ("🔬", "Methodology Review", "Breakdown of research design, methods, and procedures."),
            ("🔗", "Citation Analysis", "Reference extraction and citation relationships."),
            ("🔍", "Research Gaps", "Identification of unexplored areas and future directions."),
        ] + RESEARCH_TOOLS)

        label("Study tools")
        card_grid(STUDY_TOOLS)

        label("Technology")
        card_grid([
            ("⚡", "Streamlit", "Interactive web interface."),
            ("🤖", "Your choice of AI", "Google Gemini by default, or OpenAI, Anthropic Claude, or any OpenAI-compatible server (Groq, OpenRouter, Ollama) with your own key."),
            ("📑", "PyMuPDF & python-docx", "Document parsing and text extraction."),
            ("📈", "Plotly, Matplotlib, ReportLab", "Visualizations and report generation."),
        ])

    render_document_status(status_slot, uploaded_file, has_document)

if __name__ == "__main__":
    main()
