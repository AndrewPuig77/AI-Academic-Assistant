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

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .feature-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .analysis-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #28a745;
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