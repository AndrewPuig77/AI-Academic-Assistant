"""
Gemini AI Analyzer Module
Handles all interactions with Google's Gemini AI for research paper analysis
"""

import google.generativeai as genai
import os
import json
import logging
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """
    Handles analysis of research papers using Google's Gemini AI.
    Provides specialized prompts and analysis functions for academic content.
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini analyzer with API configuration.
        
        Args:
            model_name: Name of the Gemini model to use
        """
        self.model_name = model_name
        self.api_key = os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key or self.api_key == "your_google_api_key_here":
            raise ValueError("Please set GOOGLE_API_KEY in your .env file")
        
        # Configure Gemini API
        genai.configure(api_key=self.api_key)
        
        # List available models to debug
        try:
            available_models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    available_models.append(model.name)
            logger.info(f"Available models: {available_models}")
            
            # Use the first available Gemini model if the specified one doesn't work
            if available_models:
                # Try to find a flash model first
                flash_models = [m for m in available_models if 'flash' in m.lower()]
                if flash_models:
                    actual_model = flash_models[0]
                else:
                    actual_model = available_models[0]
                logger.info(f"Using model: {actual_model}")
            else:
                actual_model = model_name
                
        except Exception as e:
            logger.warning(f"Could not list models: {e}, using default: {model_name}")
            actual_model = model_name
        
        # Initialize model - use exact model name from API
        try:
            # Use models that are confirmed to be available based on the list_models output
            working_models = [
                "models/gemini-1.5-flash-latest",
                "models/gemini-2.0-flash-exp",
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-1.5-flash-8b-latest",
                "models/gemini-flash-latest"
            ]
            
            for test_model in working_models:
                try:
                    self.model = genai.GenerativeModel(test_model)
                    # Test the model with a very simple prompt to verify it works
                    test_response = self.model.generate_content(
                        "Hello", 
                        generation_config={
                            'temperature': 0.1,
                            'max_output_tokens': 5,
                            'top_p': 0.8,
                            'top_k': 40
                        }
                    )
                    if test_response and test_response.text:
                        logger.info(f"Successfully initialized and tested model: {test_model}")
                        actual_model = test_model
                        break
                except Exception as model_error:
                    logger.warning(f"Model {test_model} failed: {str(model_error)[:200]}")
                    continue
            else:
                raise Exception("No working model found - please check your API key quota")
                
        except Exception as e:
            logger.error(f"Failed to initialize any model: {e}")
            raise Exception(f"Could not initialize Gemini model: {e}")
        
        # Generation configuration
        self.generation_config = {
            'temperature': float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
            'max_output_tokens': int(os.getenv('GEMINI_MAX_TOKENS', '8192')),
            'top_p': 0.8,
            'top_k': 40
        }
        
        logger.info(f"Gemini analyzer initialized with model: {actual_model}")
    
    def analyze_paper(self, paper_text: str, analysis_options: Dict[str, bool]) -> Dict[str, str]:
        """
        Comprehensive analysis of a research paper.
        
        Args:
            paper_text: Extracted text from the research paper
            analysis_options: Dictionary specifying which analyses to perform
            
        Returns:
            Dictionary containing analysis results
        """
        results = {}
        
        try:
            # Generate summary if requested
            if analysis_options.get('summary', False):
                results['summary'] = self.generate_summary(paper_text)
                time.sleep(1)  # Rate limiting
            
            # Analyze methodology if requested
            if analysis_options.get('methodology', False):
                results['methodology'] = self.analyze_methodology(paper_text)
                time.sleep(1)
            
            # Extract citations if requested
            if analysis_options.get('citations', False):
                results['citations'] = self.extract_citations(paper_text)
                time.sleep(1)
            
            # Identify research gaps if requested
            if analysis_options.get('gaps', False):
                results['gaps'] = self.identify_research_gaps(paper_text)
                time.sleep(1)
            
            # Extract keywords if requested
            if analysis_options.get('keywords', False):
                results['keywords'] = self.extract_keywords(paper_text)
                time.sleep(1)
            
            # Detailed analysis if requested
            if analysis_options.get('detailed', False):
                results['detailed'] = self.detailed_analysis(paper_text)
                time.sleep(1)
            
            logger.info(f"Analysis completed with {len(results)} components")
            return results
            
        except Exception as e:
            logger.error(f"Error during paper analysis: {str(e)}")
            raise Exception(f"Analysis failed: {str(e)}")
    
    def generate_summary(self, paper_text: str) -> str:
        """Generate an intelligent summary of the research paper."""
        
        prompt = f"""
        As an expert research analyst, provide a comprehensive but concise summary of this research paper. 
        Include the following elements:

        📋 RESEARCH SUMMARY:
        • **Main Research Question/Problem**: What problem does this paper address?
        • **Key Methodology**: How did they approach the problem?
        • **Major Findings**: What are the most significant results?
        • **Practical Implications**: How can these findings be applied?
        • **Limitations**: What are the key limitations mentioned?

        Make the summary accessible to both experts and non-experts. Use clear, engaging language.
        Limit to 300-400 words.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    def analyze_methodology(self, paper_text: str) -> str:
        """Analyze the research methodology in detail."""
        
        prompt = f"""
        As a research methodology expert, analyze the research methods used in this paper. 
        Provide a detailed breakdown:

        🔬 METHODOLOGY ANALYSIS:
        • **Research Design**: What type of study is this? (experimental, observational, theoretical, etc.)
        • **Data Collection**: How was data gathered? What instruments/tools were used?
        • **Sample/Participants**: Who or what was studied? Sample size and characteristics?
        • **Analysis Methods**: What statistical or analytical methods were employed?
        • **Variables**: What were the key independent and dependent variables?
        • **Controls**: What controls or comparisons were made?
        • **Validity Considerations**: How did they ensure validity and reliability?

        Rate the methodology strength from 1-5 and explain why.
        Suggest improvements or alternative approaches.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error analyzing methodology: {str(e)}")
            return f"Error analyzing methodology: {str(e)}"
    
    def extract_citations(self, paper_text: str) -> str:
        """Extract and analyze citations and references."""
        
        prompt = f"""
        As a bibliometrics expert, analyze the citations and references in this research paper:

        📚 CITATION ANALYSIS:
        • **Key References**: List the 5-10 most important references cited
        • **Citation Patterns**: What types of sources are cited? (journals, books, conferences, etc.)
        • **Temporal Analysis**: What's the age distribution of references? Are they recent or historical?
        • **Authority Analysis**: Are there citations to seminal works or key authorities in the field?
        • **Self-Citations**: Are there any apparent self-citations by the authors?
        • **Citation Context**: How are key citations used? (supporting evidence, contradicting, building upon)

        Extract actual reference information where possible (author, title, journal, year).
        Identify the theoretical foundation the paper builds upon.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error extracting citations: {str(e)}")
            return f"Error extracting citations: {str(e)}"
    
    def identify_research_gaps(self, paper_text: str) -> str:
        """Identify research gaps and future directions."""
        
        prompt = f"""
        As a research strategist, identify research gaps and future opportunities based on this paper:

        🔍 RESEARCH GAPS & OPPORTUNITIES:
        • **Explicit Gaps**: What gaps do the authors explicitly mention?
        • **Implicit Gaps**: What gaps can you infer from the methodology or findings?
        • **Methodological Improvements**: What methodological enhancements could strengthen future research?
        • **Scale & Scope**: Could the research be expanded in scale, scope, or context?
        • **Interdisciplinary Opportunities**: What other fields could contribute to or benefit from this research?
        • **Practical Applications**: What real-world applications need further development?
        • **Replication Needs**: What aspects need validation through replication?

        Prioritize the gaps by potential impact and feasibility.
        Suggest specific research questions for future studies.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error identifying research gaps: {str(e)}")
            return f"Error identifying research gaps: {str(e)}"
    
    def extract_keywords(self, paper_text: str) -> str:
        """Extract key terms, concepts, and technical vocabulary."""
        
        prompt = f"""
        As a domain expert, extract and organize the key terminology and concepts from this research paper:

        🏷️ KEY TERMS & CONCEPTS:
        • **Primary Keywords**: The 10-15 most important terms that define this research
        • **Technical Terms**: Specialized terminology and jargon explained
        • **Theoretical Concepts**: Key theoretical frameworks or models discussed
        • **Methodological Terms**: Important methodological concepts and techniques
        • **Domain-Specific Language**: Field-specific vocabulary and acronyms
        • **Emerging Terms**: Any new terminology introduced by this research

        For each key term, provide:
        - The term itself
        - A brief definition/explanation
        - How it's used in the context of this research

        Organize by importance and thematic relevance.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return f"Error extracting keywords: {str(e)}"
    
    def detailed_analysis(self, paper_text: str) -> str:
        """Provide comprehensive detailed analysis."""
        
        prompt = f"""
        As a senior research analyst, provide a comprehensive detailed analysis of this research paper:

        📋 COMPREHENSIVE ANALYSIS:

        **1. Research Context & Significance**
        • Why is this research important?
        • How does it fit in the broader field?
        • What problem does it solve?

        **2. Strengths & Innovations**
        • What are the key strengths of this work?
        • What's novel or innovative?
        • How does it advance the field?

        **3. Critical Assessment**
        • What are potential weaknesses or limitations?
        • Are the conclusions well-supported?
        • Are there any methodological concerns?

        **4. Impact & Applications**
        • Who would benefit from these findings?
        • What are the practical implications?
        • How might this influence future research?

        **5. Overall Quality Rating**
        • Rate the paper's quality (1-10) across:
          - Novelty and significance
          - Methodological rigor
          - Clarity of presentation
          - Impact potential

        Provide specific examples and evidence for your assessments.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error in detailed analysis: {str(e)}")
            return f"Error in detailed analysis: {str(e)}"
    
    def compare_papers(self, papers_data: List[Dict[str, str]]) -> str:
        """Compare multiple research papers."""
        
        # This would be implemented for multi-paper comparison
        prompt = f"""
        As a comparative research analyst, compare and contrast these research papers:

        🔄 COMPARATIVE ANALYSIS:
        • **Research Questions**: How do the research questions relate?
        • **Methodological Approaches**: What are the similarities and differences in methods?
        • **Key Findings**: How do the findings complement or contradict each other?
        • **Theoretical Frameworks**: What theoretical foundations do they share or differ on?
        • **Strengths & Weaknesses**: Comparative strengths and limitations
        • **Synthesis**: What insights emerge from considering these papers together?

        Papers to compare: {len(papers_data)} papers provided.
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error comparing papers: {str(e)}")
            return f"Error comparing papers: {str(e)}"

# Example usage and testing
if __name__ == "__main__":
    try:
        analyzer = GeminiAnalyzer()
        print("Gemini Analyzer initialized successfully!")
        
        # Test with sample text
        sample_text = "This is a test research paper about artificial intelligence..."
        test_options = {'summary': True, 'keywords': True}
        
        # This would be used for testing
        # results = analyzer.analyze_paper(sample_text, test_options)
        # print("Test analysis completed!")
        
    except Exception as e:
        print(f"Error: {e}")