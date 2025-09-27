"""
Academic AI Assistant - Main Streamlit Application
A powerful tool for analyzing research papers and class materials using Google's Gemini AI
Supporting both research analysis and student study tools
"""

import streamlit as st
import os
import json
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom modules (will be created next)
from app.core.pdf_processor import PDFProcessor
from app.core.gemini_analyzer import GeminiAnalyzer
from app.utils.helpers import format_analysis_results, create_download_link
from app.utils.report_generator import AdvancedReportGenerator

# Page configuration
st.set_page_config(
    page_title="Academic AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for sleek black theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(135deg, #0c0c0c 0%, #1a1a1a 100%);
        color: #ffffff;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main header styling */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 30px rgba(0, 210, 255, 0.3);
        letter-spacing: -1px;
    }
    
    /* Subtitle styling */
    .stMarkdown h3 {
        color: #a0a0a0;
        text-align: center;
        font-weight: 400;
        margin-bottom: 3rem;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 100%);
        border-right: 1px solid #333;
    }
    
    /* Sidebar headers */
    .css-1d391kg h1, .css-1d391kg h2, .css-1d391kg h3 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Cards and containers */
    .feature-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        padding: 2rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        border: 1px solid #333;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        border: 1px solid #00d2ff;
        box-shadow: 0 12px 48px rgba(0, 210, 255, 0.2);
    }
    
    /* Analysis sections */
    .analysis-section {
        background: rgba(30, 30, 30, 0.8);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #333;
        backdrop-filter: blur(8px);
    }
    
    /* Success messages */
    .success-message {
        background: linear-gradient(135deg, #1a2f1a 0%, #2d4a2d 100%);
        color: #4ade80;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #4ade80;
        box-shadow: 0 4px 16px rgba(74, 222, 128, 0.2);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(20, 20, 20, 0.8);
        border-radius: 16px;
        padding: 8px;
        backdrop-filter: blur(10px);
        border: 1px solid #333;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        color: #a0a0a0;
        font-weight: 500;
        padding: 12px 24px;
        transition: all 0.3s ease;
        border: 1px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 210, 255, 0.1);
        color: #ffffff;
        border: 1px solid rgba(0, 210, 255, 0.3);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%);
        color: #ffffff !important;
        border: 1px solid #00d2ff;
        box-shadow: 0 4px 16px rgba(0, 210, 255, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%);
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 210, 255, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 210, 255, 0.4);
        background: linear-gradient(135deg, #00d2ff 0%, #2d3db5 100%);
    }
    
    /* File uploader */
    .stFileUploader > div {
        background: rgba(30, 30, 30, 0.8);
        border: 2px dashed #333;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: #00d2ff;
        background: rgba(0, 210, 255, 0.05);
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: rgba(30, 30, 30, 0.8);
        border: 1px solid #333;
        border-radius: 12px;
        color: #ffffff;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background: rgba(20, 20, 20, 0.6);
        border: 1px solid #333;
        border-top: none;
        border-radius: 0 0 12px 12px;
    }
    
    /* Metrics */
    .metric-container {
        background: rgba(30, 30, 30, 0.8);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #333;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        border-color: #00d2ff;
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 210, 255, 0.2);
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #00d2ff 0%, #3a47d5 100%);
    }
    
    /* Text inputs */
    .stTextInput > div > div > input {
        background: rgba(30, 30, 30, 0.8);
        border: 1px solid #333;
        border-radius: 8px;
        color: #ffffff;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #00d2ff;
        box-shadow: 0 0 16px rgba(0, 210, 255, 0.3);
    }
    
    /* Selectboxes */
    .stSelectbox > div > div > select {
        background: rgba(30, 30, 30, 0.8);
        border: 1px solid #333;
        color: #ffffff;
    }
    
    /* Info boxes */
    .stInfo {
        background: rgba(0, 210, 255, 0.1);
        border: 1px solid rgba(0, 210, 255, 0.3);
        border-radius: 12px;
    }
    
    /* Warning boxes */
    .stWarning {
        background: rgba(255, 193, 7, 0.1);
        border: 1px solid rgba(255, 193, 7, 0.3);
        border-radius: 12px;
    }
    
    /* Error boxes */
    .stError {
        background: rgba(220, 53, 69, 0.1);
        border: 1px solid rgba(220, 53, 69, 0.3);
        border-radius: 12px;
    }
    
    /* Success boxes */
    .stSuccess {
        background: rgba(74, 222, 128, 0.1);
        border: 1px solid rgba(74, 222, 128, 0.3);
        border-radius: 12px;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #00d2ff 0%, #3a47d5 100%);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #00b8e6 0%, #2d3db5 100%);
    }
    
    /* Glow effects */
    .glow {
        box-shadow: 0 0 20px rgba(0, 210, 255, 0.5);
    }
    
    /* Animation */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Main title with modern styling
    st.markdown('<h1 class="main-title">🎓 Academic AI Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Powered by Google Gemini AI • Research Analysis & Study Tools for Academic Success</p>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key check
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_api_key_here":
            st.error("⚠️ Please set your Google API key in the .env file")
            st.stop()
        else:
            st.success("✅ API Key configured")
        
        st.header("📋 Features")
        features = [
            "📄 Smart PDF Processing",
            "🧠 Intelligent Analysis", 
            "📊 Methodology Breakdown",
            "🔗 Citation Network",
            "🔍 Research Gap ID",
            "⚖️ Multi-Paper Compare"
        ]
        for feature in features:
            st.markdown(f"- {feature}")
    
    # Main content area
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📤 Upload & Analyze", "📊 Results", "🔬 Research Tools", "📚 Study Tools", "ℹ️ About"])
    
    with tab1:
        st.header("Upload Your Research Paper")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=['pdf'],
            help="Upload a research paper in PDF format (max 10MB)"
        )
        
        if uploaded_file is not None:
            # Display file info
            st.markdown(f"**File:** {uploaded_file.name}")
            st.markdown(f"**Size:** {uploaded_file.size / 1024 / 1024:.2f} MB")
            
            # Analysis options
            st.subheader("Analysis Options")
            col1, col2 = st.columns(2)
            
            with col1:
                include_summary = st.checkbox("📝 Generate Summary", value=True)
                include_methodology = st.checkbox("🔬 Analyze Methodology", value=True)
                include_citations = st.checkbox("📚 Extract Citations", value=True)
            
            with col2:
                include_gaps = st.checkbox("🔍 Identify Research Gaps", value=True)
                include_keywords = st.checkbox("🏷️ Extract Keywords", value=True)
                detailed_analysis = st.checkbox("📋 Detailed Analysis", value=False)
            
            # Analyze button
            if st.button("🚀 Analyze Paper", type="primary", use_container_width=True):
                try:
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Step 1: Initialize processors
                    status_text.text("🔧 Initializing AI processors...")
                    progress_bar.progress(10)
                    pdf_processor = PDFProcessor()
                    analyzer = GeminiAnalyzer()
                    
                    # Step 2: Save uploaded file
                    status_text.text("💾 Saving uploaded file...")
                    progress_bar.progress(20)
                    temp_path = f"uploads/{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.read())
                    
                    # Step 3: Extract text from PDF
                    status_text.text("📄 Extracting text from PDF...")
                    progress_bar.progress(40)
                    extracted_text = pdf_processor.extract_text(temp_path)
                    
                    # Step 4: Prepare analysis options
                    status_text.text("⚙️ Configuring analysis options...")
                    progress_bar.progress(50)
                    analysis_options = {
                        'summary': include_summary,
                        'methodology': include_methodology,
                        'citations': include_citations,
                        'gaps': include_gaps,
                        'keywords': include_keywords,
                        'detailed': detailed_analysis
                    }
                    
                    # Step 5: AI Analysis (longest step)
                    status_text.text("🧠 Analyzing with Google Gemini AI... (this may take a moment)")
                    progress_bar.progress(60)
                    analysis_results = analyzer.analyze_paper(extracted_text, analysis_options)
                    progress_bar.progress(85)
                    
                    # Step 6: Store results
                    status_text.text("💾 Saving analysis results...")
                    progress_bar.progress(95)
                    st.session_state['analysis_results'] = analysis_results
                    st.session_state['analyzed_content'] = extracted_text
                    st.session_state['paper_name'] = uploaded_file.name
                    
                    # Step 7: Clean up
                    status_text.text("🧹 Cleaning up temporary files...")
                    progress_bar.progress(100)
                    os.remove(temp_path)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    st.markdown('<div class="success-message">✅ Analysis complete! Check the Results tab.</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {str(e)}")
    
    with tab2:
        st.header("Analysis Results")
        
        if 'analysis_results' in st.session_state:
            results = st.session_state['analysis_results']
            paper_name = st.session_state.get('paper_name', 'Unknown Paper')
            
            st.markdown(f"### Results for: **{paper_name}**")
            
            # Display results based on what was analyzed
            if results.get('summary'):
                with st.expander("📝 Paper Summary", expanded=True):
                    st.markdown(results['summary'])
            
            if results.get('methodology'):
                with st.expander("🔬 Methodology Analysis"):
                    st.markdown(results['methodology'])
            
            if results.get('citations'):
                with st.expander("📚 Citations & References"):
                    st.markdown(results['citations'])
            
            if results.get('gaps'):
                with st.expander("🔍 Research Gaps Identified"):
                    st.markdown(results['gaps'])
            
            if results.get('keywords'):
                with st.expander("🏷️ Key Terms & Concepts"):
                    st.markdown(results['keywords'])
            
            if results.get('detailed'):
                with st.expander("📋 Detailed Analysis"):
                    st.markdown(results['detailed'])
            
            # Export options
            st.subheader("📤 Export Results")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 Download as Text"):
                    formatted_results = format_analysis_results(results, paper_name)
                    st.download_button(
                        label="📄 Download Analysis",
                        data=formatted_results,
                        file_name=f"analysis_{paper_name.replace('.pdf', '.txt')}",
                        mime='text/plain'
                    )
            
            with col2:
                if st.button("📊 Generate Report"):
                    # Initialize the advanced report generator
                    report_generator = AdvancedReportGenerator()
                    
                    # Display the advanced interactive report
                    report_generator.display_streamlit_report(results, paper_name)
        
        else:
            st.info("📤 Upload and analyze a paper first to see results here.")
    
    with tab3:
        st.header("🔬 Advanced Research Tools")
        
        if st.session_state.get('analyzed_content') and st.session_state.get('analysis_results'):
            st.markdown("### 🚀 AI-Powered Research Assistant")
            st.markdown("Generate advanced insights and research directions based on your analyzed paper.")
            
            # Create columns for the research tools
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔍 Find Related Papers", use_container_width=True):
                    with st.spinner("🔍 Analyzing research landscape..."):
                        analyzer = GeminiAnalyzer()
                        related_papers = analyzer.suggest_related_papers(st.session_state.analyzed_content)
                        st.session_state['related_papers'] = related_papers
                
                if st.button("❓ Generate Research Questions", use_container_width=True):
                    with st.spinner("❓ Generating research questions..."):
                        analyzer = GeminiAnalyzer()
                        research_questions = analyzer.generate_research_questions(st.session_state.analyzed_content)
                        st.session_state['research_questions'] = research_questions
            
            with col2:
                if st.button("💡 Build New Hypotheses", use_container_width=True):
                    with st.spinner("💡 Building hypotheses..."):
                        analyzer = GeminiAnalyzer()
                        hypotheses = analyzer.build_hypotheses(st.session_state.analyzed_content)
                        st.session_state['hypotheses'] = hypotheses
                
                if st.button("📋 Draft Research Proposal", use_container_width=True):
                    with st.spinner("📋 Drafting research proposal..."):
                        analyzer = GeminiAnalyzer()
                        proposal = analyzer.generate_research_proposal(st.session_state.analyzed_content)
                        st.session_state['research_proposal'] = proposal
            
            # Display results
            if 'related_papers' in st.session_state:
                with st.expander("🔍 Related Papers & Research Areas", expanded=True):
                    st.markdown(st.session_state.related_papers)
                    st.download_button(
                        label="📥 Download Related Papers Guide",
                        data=st.session_state.related_papers,
                        file_name="related_papers_guide.txt",
                        mime="text/plain"
                    )
            
            if 'research_questions' in st.session_state:
                with st.expander("❓ Generated Research Questions", expanded=True):
                    st.markdown(st.session_state.research_questions)
                    st.download_button(
                        label="📥 Download Research Questions",
                        data=st.session_state.research_questions,
                        file_name="research_questions.txt",
                        mime="text/plain"
                    )
            
            if 'hypotheses' in st.session_state:
                with st.expander("💡 New Hypotheses", expanded=True):
                    st.markdown(st.session_state.hypotheses)
                    st.download_button(
                        label="📥 Download Hypotheses",
                        data=st.session_state.hypotheses,
                        file_name="research_hypotheses.txt",
                        mime="text/plain"
                    )
            
            if 'research_proposal' in st.session_state:
                with st.expander("📋 Research Proposal Draft", expanded=True):
                    st.markdown(st.session_state.research_proposal)
                    st.download_button(
                        label="📥 Download Proposal Draft",
                        data=st.session_state.research_proposal,
                        file_name="research_proposal_draft.txt",
                        mime="text/plain"
                    )
        
        else:
            st.info("📤 Upload and analyze a paper first to access advanced research tools.")
            st.markdown("""
            ### 🛠️ Available Research Tools:
            
            **🔍 Related Paper Suggestions**
            - Find similar research and key papers to explore
            - Get search strategies and keywords
            - Discover cross-disciplinary connections
            
            **❓ Research Question Generator** 
            - Generate meaningful questions for future investigation
            - Identify methodological improvements
            - Explore broader implications
            
            **💡 Hypothesis Builder**
            - Develop testable hypotheses from findings
            - Suggest novel applications and extensions  
            - Propose alternative explanations
            
            **📋 Research Proposal Assistant**
            - Draft compelling research proposal outlines
            - Structure objectives and methodology
            - Align with grant application requirements
            """)
    
    with tab4:
        st.header("📚 Study Tools for Class Materials")
        
        # Check if material has been analyzed
        if not (st.session_state.get('analyzed_content') and st.session_state.get('analysis_results')):
            st.info("📤 Upload and analyze class material first to access study tools.")
            st.markdown("""
            ### 🎓 What Study Tools Can Do:
            
            **📇 Smart Flashcards**
            - Extract key definitions and concepts
            - Create active recall questions
            - Export as printable cards
            
            **❓ Practice Questions**
            - Multiple choice questions
            - Short answer prompts  
            - Essay question ideas
            
            **📖 Study Guides**
            - Organized topic summaries
            - Key concept hierarchies
            - Quick review checklists
            
            **📊 Material Analysis**
            - Difficulty assessment
            - Study recommendations
            - Exam focus predictions
            """)
        else:
            # Material has been analyzed - show study tools
            material_name = st.session_state.get('paper_name', 'Class Material')
            analyzed_content = st.session_state.get('analyzed_content', '')
            
            st.success(f"✅ Class material loaded: {material_name}")
            
            # Study Tools Options
            st.subheader("🛠️ Choose Your Study Tool")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📇 Generate Flashcards", use_container_width=True):
                    with st.spinner("🧠 Creating educational flashcards..."):
                        try:
                            analyzer = GeminiAnalyzer()
                            flashcards_result = analyzer.generate_flashcards(analyzed_content)
                            
                            st.session_state['study_flashcards'] = flashcards_result
                            st.success("🎉 Flashcards generated successfully!")
                            
                        except Exception as e:
                            st.error(f"❌ Error generating flashcards: {str(e)}")
                
                if st.button("❓ Create Practice Questions", use_container_width=True):
                    with st.spinner("📝 Creating practice questions..."):
                        try:
                            analyzer = GeminiAnalyzer()
                            
                            # Question type selection
                            question_types = st.multiselect(
                                "Select question types:",
                                ["multiple_choice", "short_answer", "essay"],
                                default=["multiple_choice", "short_answer"],
                                key="question_types_selector"
                            )
                            
                            if question_types:
                                questions_result = analyzer.create_practice_questions(
                                    analyzed_content, question_types
                                )
                                st.session_state['study_questions'] = questions_result
                                st.success("🎯 Practice questions created!")
                            
                        except Exception as e:
                            st.error(f"❌ Error creating questions: {str(e)}")
            
            with col2:
                if st.button("📖 Build Study Guide", use_container_width=True):
                    with st.spinner("📚 Building comprehensive study guide..."):
                        try:
                            analyzer = GeminiAnalyzer()
                            
                            # Get topic name from user or use filename
                            topic_name = st.text_input(
                                "Topic/Chapter name (optional):",
                                value=material_name.replace('.pdf', ''),
                                key="study_guide_topic"
                            ) or material_name
                            
                            study_guide_result = analyzer.build_study_guide(
                                analyzed_content, topic_name
                            )
                            st.session_state['study_guide'] = study_guide_result
                            st.success("📋 Study guide created!")
                            
                        except Exception as e:
                            st.error(f"❌ Error building study guide: {str(e)}")
                
                if st.button("📊 Analyze Material", use_container_width=True):
                    with st.spinner("🔍 Analyzing class material..."):
                        try:
                            analyzer = GeminiAnalyzer()
                            
                            material_type = st.selectbox(
                                "Material type:",
                                ["textbook", "lecture_notes", "assignment", "handout", "other"],
                                key="material_type_selector"
                            )
                            
                            analysis_result = analyzer.analyze_class_material(
                                analyzed_content, material_type
                            )
                            st.session_state['material_analysis'] = analysis_result
                            st.success("🎯 Material analysis complete!")
                            
                        except Exception as e:
                            st.error(f"❌ Error analyzing material: {str(e)}")
            
            # Display Results Section
            st.markdown("---")
            st.subheader("📋 Study Tool Results")
            
            # Flashcards Display
            if 'study_flashcards' in st.session_state:
                with st.expander("📇 Generated Flashcards", expanded=False):
                    flashcards_text = st.session_state['study_flashcards']
                    
                    try:
                        # Try to parse JSON flashcards
                        import json
                        import re
                        
                        # Extract JSON from response
                        json_match = re.search(r'\[(.*?)\]', flashcards_text, re.DOTALL)
                        if json_match:
                            json_str = '[' + json_match.group(1) + ']'
                            flashcards = json.loads(json_str)
                            
                            st.success(f"📊 Generated {len(flashcards)} flashcards")
                            
                            # Display flashcards in an interactive format
                            for i, card in enumerate(flashcards, 1):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**Card {i} - Front:**")
                                    st.info(card.get('front', 'No front text'))
                                with col2:
                                    st.markdown(f"**Card {i} - Back:**")
                                    st.success(card.get('back', 'No back text'))
                                
                                if i < len(flashcards):
                                    st.markdown("---")
                        else:
                            st.markdown("**Raw Flashcards:**")
                            st.markdown(flashcards_text)
                            
                    except Exception as e:
                        st.markdown("**Generated Flashcards:**")
                        st.markdown(flashcards_text)
            
            # Practice Questions Display
            if 'study_questions' in st.session_state:
                with st.expander("❓ Practice Questions", expanded=False):
                    st.markdown(st.session_state['study_questions'])
            
            # Study Guide Display
            if 'study_guide' in st.session_state:
                with st.expander("📖 Study Guide", expanded=False):
                    st.markdown(st.session_state['study_guide'])
            
            # Material Analysis Display
            if 'material_analysis' in st.session_state:
                with st.expander("📊 Material Analysis", expanded=False):
                    analysis_data = st.session_state['material_analysis']
                    if isinstance(analysis_data, dict):
                        st.markdown(f"**Material Type:** {analysis_data.get('material_type', 'Unknown')}")
                        st.markdown(f"**Content Length:** {analysis_data.get('content_length', 0)} characters")
                        st.markdown("**Analysis:**")
                        st.markdown(analysis_data.get('analysis', 'No analysis available'))
                    else:
                        st.markdown(analysis_data)
            
            # Export Section
            if any(key in st.session_state for key in ['study_flashcards', 'study_questions', 'study_guide', 'material_analysis']):
                st.markdown("---")
                st.subheader("📥 Export Study Materials")
                
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if 'study_flashcards' in st.session_state:
                        if st.button("📇 Export Flashcards", use_container_width=True):
                            try:
                                # Create downloadable flashcards text file
                                flashcards_text = st.session_state['study_flashcards']
                                
                                # Try to format as structured text
                                try:
                                    json_match = re.search(r'\[(.*?)\]', flashcards_text, re.DOTALL)
                                    if json_match:
                                        json_str = '[' + json_match.group(1) + ']'
                                        flashcards = json.loads(json_str)
                                        
                                        formatted_text = f"FLASHCARDS - {material_name}\n"
                                        formatted_text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                        
                                        for i, card in enumerate(flashcards, 1):
                                            formatted_text += f"CARD {i}\n"
                                            formatted_text += f"Front: {card.get('front', '')}\n"
                                            formatted_text += f"Back: {card.get('back', '')}\n\n"
                                        
                                        st.download_button(
                                            label="💾 Download Flashcards.txt",
                                            data=formatted_text,
                                            file_name=f"flashcards_{material_name.replace('.pdf', '')}.txt",
                                            mime="text/plain"
                                        )
                                    else:
                                        st.download_button(
                                            label="💾 Download Flashcards.txt",
                                            data=flashcards_text,
                                            file_name=f"flashcards_{material_name.replace('.pdf', '')}.txt",
                                            mime="text/plain"
                                        )
                                except:
                                    st.download_button(
                                        label="💾 Download Flashcards.txt",
                                        data=flashcards_text,
                                        file_name=f"flashcards_{material_name.replace('.pdf', '')}.txt",
                                        mime="text/plain"
                                    )
                                
                            except Exception as e:
                                st.error(f"❌ Export error: {str(e)}")
                
                with export_col2:
                    if 'study_questions' in st.session_state:
                        if st.button("❓ Export Questions", use_container_width=True):
                            try:
                                questions_text = st.session_state['study_questions']
                                formatted_questions = f"PRACTICE QUESTIONS - {material_name}\n"
                                formatted_questions += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                formatted_questions += questions_text
                                
                                st.download_button(
                                    label="💾 Download Questions.txt",
                                    data=formatted_questions,
                                    file_name=f"questions_{material_name.replace('.pdf', '')}.txt",
                                    mime="text/plain"
                                )
                                
                            except Exception as e:
                                st.error(f"❌ Export error: {str(e)}")
                
                with export_col3:
                    if 'study_guide' in st.session_state:
                        if st.button("📖 Export Study Guide", use_container_width=True):
                            try:
                                guide_text = st.session_state['study_guide']
                                formatted_guide = f"STUDY GUIDE - {material_name}\n"
                                formatted_guide += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                                formatted_guide += guide_text
                                
                                st.download_button(
                                    label="💾 Download Study Guide.txt",
                                    data=formatted_guide,
                                    file_name=f"study_guide_{material_name.replace('.pdf', '')}.txt",
                                    mime="text/plain"
                                )
                                
                            except Exception as e:
                                st.error(f"❌ Export error: {str(e)}")
                
                # Combined Export
                st.markdown("---")
                if st.button("📦 Export All Study Materials", use_container_width=True):
                    try:
                        combined_content = f"COMPLETE STUDY PACKAGE - {material_name}\n"
                        combined_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
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
                            label="💾 Download Complete Study Package.txt",
                            data=combined_content,
                            file_name=f"study_package_{material_name.replace('.pdf', '')}.txt",
                            mime="text/plain"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Export error: {str(e)}")
    
    with tab5:
        st.header("About Academic AI Assistant")
        
        st.markdown("""
        ### 🎯 Purpose
        This tool leverages Google's Gemini AI to provide comprehensive analysis of research papers AND class materials,
        helping researchers, students, and academics quickly understand complex documents and create effective study materials.
        
        ### 🚀 Key Features
        """)
        
        features_detail = {
            "📄 Smart PDF Processing": "Advanced text extraction from research papers and class materials with structure preservation",
            "🧠 Intelligent Analysis": "AI-powered content analysis using Google Gemini's language understanding",
            "📊 Methodology Breakdown": "Detailed extraction and explanation of research methods and procedures",
            "🔗 Citation Network": "Automatic extraction of references and citation relationships",
            "🔍 Research Gap Identification": "AI identification of unexplored areas and future research directions",
            "⚖️ Multi-Paper Comparison": "Side-by-side analysis and comparison of multiple research papers",
            "🔬 Related Paper Suggestions": "AI-powered discovery of similar research and strategic search guidance",
            "❓ Research Question Generator": "Automatic generation of meaningful research questions for future investigation",
            "💡 Hypothesis Builder": "Development of testable hypotheses and alternative explanations from findings",
            "📋 Research Proposal Assistant": "AI-assisted drafting of compelling research proposal outlines and grant applications",
            "📇 Smart Flashcards": "Extract key definitions and concepts from class materials for active recall studying",
            "🎯 Practice Questions": "Generate multiple choice, short answer, and essay questions from course content",
            "📚 Study Guides": "Create comprehensive study guides with organized topics, summaries, and review checklists",
            "📊 Material Analysis": "Analyze difficulty levels, study recommendations, and exam focus predictions for class materials"
        }
        
        for feature, description in features_detail.items():
            st.markdown(f"**{feature}**")
            st.markdown(f"_{description}_")
            st.markdown("---")
        
        st.markdown("""
        ### � Free Tier Information
        
        **This application uses Google Gemini's generous free tier:**
        
        - ✨ **Gemini 1.5 Flash**: 1,500 requests per day (likely what you're using)
        - 🧠 **Gemini 2.5 Pro**: 100 requests per day  
        - 📊 **Analysis Capacity**: Analyze 250-500 research papers daily!
        - 🔄 **Usage**: Each analysis uses 3-6 API requests depending on options selected
        - ⏰ **Reset**: Quota resets daily at midnight UTC
        
        **Model Selection**: The app automatically selects the best available model for optimal performance.
        
        ---
        
        ### �🛠️ Technology Stack
        - **Frontend**: Streamlit web framework with sleek black theme
        - **AI Engine**: Google Gemini AI (1.5/2.0 Flash models)
        - **PDF Processing**: PyMuPDF (fitz) for text extraction
        - **Data Visualization**: Plotly, Matplotlib, Seaborn, WordCloud
        - **Data Analysis**: Pandas, NumPy for data manipulation
        - **Report Generation**: ReportLab for PDF exports
        - **Environment**: Python 3.13, python-dotenv for configuration
        - **Optional APIs**: FastAPI, Uvicorn for REST capabilities
        """)

if __name__ == "__main__":
    main()