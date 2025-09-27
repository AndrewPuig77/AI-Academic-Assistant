"""
AI Research Paper Assistant - Main Streamlit Application
A powerful tool for analyzing research papers using Google's Gemini AI
"""

import streamlit as st
import os
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
    page_title="AI Research Paper Assistant",
    page_icon="📚",
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
    # Main header
    st.markdown('<h1 class="main-header">📚 AI Research Paper Assistant</h1>', unsafe_allow_html=True)
    st.markdown("### Powered by Google Gemini AI - Analyze research papers like never before!")
    
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
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "📊 Results", "ℹ️ About"])
    
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
        st.header("About AI Research Paper Assistant")
        
        st.markdown("""
        ### 🎯 Purpose
        This tool leverages Google's Gemini AI to provide comprehensive analysis of research papers,
        helping researchers, students, and academics quickly understand complex scientific documents.
        
        ### 🚀 Key Features
        """)
        
        features_detail = {
            "📄 Smart PDF Processing": "Advanced text extraction from research papers with structure preservation",
            "🧠 Intelligent Analysis": "AI-powered content analysis using Google Gemini's language understanding",
            "📊 Methodology Breakdown": "Detailed extraction and explanation of research methods and procedures",
            "🔗 Citation Network": "Automatic extraction of references and citation relationships",
            "🔍 Research Gap Identification": "AI identification of unexplored areas and future research directions",
            "⚖️ Multi-Paper Comparison": "Side-by-side analysis and comparison of multiple research papers"
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
        - **Frontend**: Streamlit
        - **AI Engine**: Google Gemini AI
        - **PDF Processing**: PyMuPDF
        - **Data Visualization**: Plotly & NetworkX
        
        ### 📞 Support
        For questions or issues, please check the documentation or contact support.
        """)

if __name__ == "__main__":
    main()