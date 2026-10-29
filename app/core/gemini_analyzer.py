"""
Gemini AI Analyzer Module
Handles all interactions with Google's Gemini AI for research paper analysis
"""

from google import genai
from google.genai import errors as genai_errors
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

class GeminiAPIKeyError(Exception):
    """Raised when Gemini rejects the configured API key."""


class GeminiModel:
    """
    Thin wrapper around the google-genai client that keeps the
    model.generate_content(prompt, generation_config=...) / response.text interface
    used throughout GeminiAnalyzer, and falls back to another model when one is retired.
    """

    # Tried in order after any configured model; aliases keep working as Google releases new models
    FALLBACK_MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]

    # Model that last worked, shared across instances so later requests skip retired models
    _resolved_model: Optional[str] = None

    def __init__(self, api_key: str, preferred_model: Optional[str] = None):
        self.client = genai.Client(api_key=api_key)
        candidates = [preferred_model] if preferred_model else []
        candidates += self.FALLBACK_MODELS
        self.candidates = [m.removeprefix("models/") for m in dict.fromkeys(candidates)]

    def _models_to_try(self) -> List[str]:
        if GeminiModel._resolved_model:
            return [GeminiModel._resolved_model]
        return self.candidates

    def _discover_flash_model(self) -> Optional[str]:
        """Ask the API for any available Flash model when none of the known names work."""
        try:
            for model in self.client.models.list():
                name = model.name.removeprefix("models/")
                actions = getattr(model, "supported_actions", None) or []
                if "flash" in name and "generateContent" in actions and name not in self.candidates:
                    return name
        except Exception as e:
            logger.warning(f"Could not list Gemini models: {e}")
        return None

    def generate_content(self, prompt: str, generation_config: Optional[Dict[str, Any]] = None):
        models = self._models_to_try()
        last_error = None

        for attempt_discovery in (False, True):
            if attempt_discovery:
                discovered = self._discover_flash_model()
                if not discovered:
                    break
                models = [discovered]

            for model in models:
                try:
                    response = self.client.models.generate_content(
                        model=model, contents=prompt, config=generation_config
                    )
                    if GeminiModel._resolved_model != model:
                        logger.info(f"Using Gemini model: {model}")
                        GeminiModel._resolved_model = model
                    return GeminiResponse(response)
                except genai_errors.ClientError as e:
                    message = str(e)
                    if e.code in (401, 403) or "API_KEY_INVALID" in message or "API key not valid" in message:
                        raise GeminiAPIKeyError(
                            "Gemini rejected the API key. Check GOOGLE_API_KEY in your Streamlit secrets or .env file."
                        ) from e
                    if e.code == 404 or "not found" in message.lower() or "not supported" in message.lower():
                        logger.warning(f"Gemini model {model} unavailable, trying next: {message[:200]}")
                        if GeminiModel._resolved_model == model:
                            GeminiModel._resolved_model = None
                        last_error = e
                        continue
                    raise

        raise Exception(f"No available Gemini model found. Last error: {last_error}")


class GeminiResponse:
    """Response wrapper whose .text is always a string, as the analyzer methods expect."""

    def __init__(self, response):
        self._response = response

    @property
    def text(self) -> str:
        text = self._response.text
        if text:
            return text
        finish_reason = None
        try:
            finish_reason = self._response.candidates[0].finish_reason
        except (AttributeError, IndexError, TypeError):
            pass
        return f"⚠️ Gemini returned no text (finish reason: {finish_reason}). Try again or reduce the document size."


class GeminiAnalyzer:
    """
    Handles analysis of research papers using Google's Gemini AI.
    Provides specialized prompts and analysis functions for academic content.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize Gemini analyzer with API configuration.

        Args:
            model_name: Preferred Gemini model. Defaults to GEMINI_MODEL, then current Flash models.
        """
        # Try to get API key from Streamlit secrets first, then environment
        self.api_key = None
        try:
            import streamlit as st
            self.api_key = st.secrets.get("GOOGLE_API_KEY")
        except:
            pass
        self.api_key = self.api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key or self.api_key == "your_google_api_key_here":
            raise ValueError("Please set GOOGLE_API_KEY in Streamlit secrets or .env file")

        self.model = GeminiModel(self.api_key, model_name or os.getenv("GEMINI_MODEL"))

        # Generation configuration
        self.generation_config = {
            'temperature': float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
            'max_output_tokens': int(os.getenv('GEMINI_MAX_TOKENS', '8192')),
            'top_p': 0.8,
            'top_k': 40
        }
    
    def _make_api_call_with_retry(self, prompt: str, max_retries: int = 5, operation_name: str = "API call") -> str:
        """
        Make API call with intelligent retry logic for quota errors.
        
        Args:
            prompt: The prompt to send to the model
            max_retries: Maximum number of retries (default 5)
            operation_name: Name of the operation for logging
            
        Returns:
            Generated text response
        """
        for attempt in range(max_retries + 1):
            try:
                response = self.model.generate_content(prompt, generation_config=self.generation_config)
                if response and response.text:
                    if attempt > 0:
                        logger.info(f"✅ {operation_name} succeeded on attempt {attempt + 1}")
                    return response.text
                else:
                    return f"⚠️ No response generated for {operation_name}"

            except GeminiAPIKeyError:
                # Retrying can't fix a bad key; surface it immediately
                raise

            except Exception as e:
                error_msg = str(e)
                
                # Check for quota/rate limit errors (429 status)
                if ("429" in error_msg or "quota" in error_msg.lower() or 
                    "rate limit" in error_msg.lower() or "exceeded" in error_msg.lower()):
                    
                    if attempt < max_retries:
                        # Progressive backoff: 2, 5, 10, 20, 40 seconds
                        wait_time = min(2 ** (attempt + 1), 40)
                        logger.warning(f"🔄 {operation_name} - Quota exceeded, attempt {attempt + 1}/{max_retries + 1}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ {operation_name} failed after {max_retries + 1} attempts")
                        return f"⚠️ **API Quota Exceeded**\n\nThe Gemini API free tier has reached its daily limit (50 requests). This is normal for free accounts.\n\n**Solutions:**\n• Wait 24 hours for quota reset\n• Upgrade to paid API plan for higher limits\n• Try using fewer analysis options at once\n\n**Note:** Your document was processed successfully, but AI analysis is temporarily limited."
                
                # Other errors (not quota related)
                else:
                    if attempt < max_retries:
                        wait_time = 2 * (attempt + 1)  # Simple backoff for other errors
                        logger.warning(f"🔄 {operation_name} error (attempt {attempt + 1}/{max_retries + 1}): {error_msg}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ {operation_name} failed: {error_msg}")
                        return f"❌ **Error in {operation_name}**\n\n{error_msg}\n\nPlease try again or contact support if the issue persists."
        
        return f"❌ Failed to complete {operation_name} after {max_retries + 1} attempts"
    
    def analyze_paper(self, paper_text: str, analysis_options: Dict[str, bool]) -> Dict[str, str]:
        """
        Comprehensive analysis of academic content.
        
        Args:
            paper_text: Extracted text from the document
            analysis_options: Dictionary specifying which analyses to perform
            
        Returns:
            Dictionary containing analysis results
        """
        results = {}
        document_type = analysis_options.get('document_type', '📖 Other Academic Material')
        
        # Store document type in results for later use
        results['document_type'] = document_type
        
        try:
            # Generate summary if requested
            if analysis_options.get('summary', False):
                results['summary'] = self.generate_summary(paper_text, document_type)
                time.sleep(1)  # Rate limiting
            
            # Research paper specific analyses
            if analysis_options.get('methodology', False):
                results['methodology'] = self.analyze_methodology(paper_text)
                time.sleep(1)
            
            if analysis_options.get('gaps', False):
                results['gaps'] = self.identify_research_gaps(paper_text)
                time.sleep(1)
                
            if analysis_options.get('future_work', False):
                results['future_work'] = self.suggest_future_research(paper_text)
                time.sleep(1)
            
            # Study material specific analyses
            if analysis_options.get('concepts', False):
                results['concepts'] = self.extract_key_concepts(paper_text, document_type)
                time.sleep(1)
                
            if analysis_options.get('examples', False):
                results['examples'] = self.extract_examples_cases(paper_text, document_type)
                time.sleep(1)
                
            if analysis_options.get('questions', False):
                results['questions'] = self.generate_study_questions(paper_text, document_type)
                time.sleep(1)
                
            if analysis_options.get('difficulty', False):
                results['difficulty'] = self.assess_difficulty(paper_text, document_type)
                time.sleep(1)
            
            # Assignment/Essay specific analyses
            if analysis_options.get('structure', False):
                results['structure'] = self.analyze_structure(paper_text, document_type)
                time.sleep(1)
                
            if analysis_options.get('arguments', False):
                results['arguments'] = self.analyze_arguments(paper_text, document_type)
                time.sleep(1)
                
            if analysis_options.get('improvements', False):
                results['improvements'] = self.suggest_improvements(paper_text, document_type)
                time.sleep(1)
            
            # Report/Guide specific analyses
            if analysis_options.get('findings', False):
                results['findings'] = self.extract_findings(paper_text, document_type)
                time.sleep(1)
                
            if analysis_options.get('recommendations', False):
                results['recommendations'] = self.extract_recommendations(paper_text, document_type)
                time.sleep(1)
            
            # General analyses
            if analysis_options.get('main_points', False):
                results['main_points'] = self.extract_main_points(paper_text, document_type)
                time.sleep(1)
                
            if analysis_options.get('context', False):
                results['context'] = self.analyze_context(paper_text, document_type)
                time.sleep(1)
            
            # Extract citations/references if requested
            if analysis_options.get('citations', False):
                results['citations'] = self.extract_citations(paper_text, document_type)
                time.sleep(1)
            
            # Extract keywords if requested
            if analysis_options.get('keywords', False):
                results['keywords'] = self.extract_keywords(paper_text, document_type)
                time.sleep(1)
            
            # Detailed analysis if requested
            if analysis_options.get('detailed', False):
                results['detailed'] = self.detailed_analysis(paper_text, document_type)
                time.sleep(1)
            
            logger.info(f"Analysis completed with {len(results)} components")
            return results
            
        except Exception as e:
            logger.error(f"Error during document analysis: {str(e)}")
            raise Exception(f"Analysis failed: {str(e)}")
    
    def generate_summary(self, paper_text: str, document_type: str = "🔬 Research Paper") -> str:
        """Generate an intelligent summary based on document type."""
        
        if "Research Paper" in document_type:
            # Research paper summary
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
        elif document_type in ["📚 Textbook Chapter", "📝 Lecture Notes", "🗒️ Class Handout"]:
            # Study material summary
            prompt = f"""
            As an educational content expert, provide a clear summary of this study material. 
            Focus on the learning objectives and key educational content:

            📚 CONTENT SUMMARY:
            • **Topic/Subject**: What is this content teaching?
            • **Key Concepts**: What are the main ideas or principles explained?
            • **Learning Objectives**: What should students understand after reading this?
            • **Practical Applications**: How are these concepts used in practice?
            • **Prerequisites**: What background knowledge is assumed?

            Write the summary in a student-friendly way that helps with understanding and retention.
            Limit to 300-400 words.

            STUDY MATERIAL TEXT:
            {paper_text[:4000]}
            """
        elif document_type in ["📋 Assignment/Homework", "📄 Article/Essay"]:
            # Assignment/Essay summary
            prompt = f"""
            As an academic writing expert, provide a summary of this assignment or essay content:

            📝 CONTENT SUMMARY:
            • **Main Topic/Theme**: What is this piece about?
            • **Key Arguments/Points**: What are the primary arguments or points made?
            • **Structure**: How is the content organized?
            • **Purpose/Objective**: What is the goal of this writing?
            • **Target Audience**: Who is this written for?

            Focus on the logical flow and argumentation structure.
            Limit to 300-400 words.

            CONTENT TEXT:
            {paper_text[:4000]}
            """
        elif document_type in ["📊 Report/Thesis", "🎓 Study Guide"]:
            # Report/Guide summary
            prompt = f"""
            As a technical writing expert, provide a summary of this report or guide:

            📊 DOCUMENT SUMMARY:
            • **Purpose/Objective**: What is this document trying to accomplish?
            • **Scope**: What topics or areas does it cover?
            • **Key Findings/Points**: What are the main conclusions or recommendations?
            • **Structure**: How is the information organized?
            • **Intended Use**: How should readers use this information?

            Emphasize practical takeaways and actionable information.
            Limit to 300-400 words.

            DOCUMENT TEXT:
            {paper_text[:4000]}
            """
        else:
            # General academic material summary
            prompt = f"""
            As an academic content expert, provide a clear summary of this academic material:

            📖 CONTENT SUMMARY:
            • **Main Topic**: What is the primary subject matter?
            • **Key Points**: What are the most important ideas presented?
            • **Structure**: How is the content organized?
            • **Educational Value**: What can readers learn from this?
            • **Context**: What field or discipline does this relate to?

            Provide a balanced overview that captures the essential information.
            Limit to 300-400 words.

            ACADEMIC TEXT:
            {paper_text[:4000]}
            """
        
        return self._make_api_call_with_retry(prompt, max_retries=5, operation_name="summary generation")
    
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
        
        return self._make_api_call_with_retry(prompt, max_retries=5, operation_name="methodology analysis")
    
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
    
    def detailed_analysis(self, paper_text: str, document_type: str = "🔬 Research Paper") -> str:
        """Provide comprehensive detailed analysis based on document type."""
        
        if "Research Paper" in document_type:
            # Research paper detailed analysis
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
        else:
            # Study material detailed analysis
            prompt = f"""
            As an educational content expert, provide a comprehensive analysis of this study material:

            📚 COMPREHENSIVE STUDY MATERIAL ANALYSIS:

            **1. Educational Value & Learning Objectives**
            • What are the primary learning objectives?
            • How well does the content achieve these goals?
            • What knowledge level is this appropriate for?

            **2. Content Quality & Organization**
            • How well is the information organized?
            • Are explanations clear and comprehensive?
            • What are the content strengths?

            **3. Pedagogical Assessment**
            • Are concepts explained progressively?
            • Are examples and illustrations effective?
            • What could improve understanding?

            **4. Practical Application**
            • How can students apply this knowledge?
            • What real-world connections are made?
            • What study strategies would work best?

            **5. Study Recommendations**
            • Difficulty level assessment (1-10)
            • Key concepts to focus on
            • Best study approaches
            • Time investment needed

            Focus on practical study and learning insights.

            STUDY MATERIAL TEXT:
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
    
    def suggest_related_papers(self, paper_text: str) -> str:
        """Generate suggestions for related papers and research areas."""
        
        prompt = f"""
        As a research librarian and academic expert, analyze this research paper and suggest related papers, topics, and search strategies:

        🔍 RELATED RESEARCH SUGGESTIONS:

        **1. Key Research Areas & Keywords**
        • Primary research domain and subfields
        • Important technical keywords for searches
        • Alternative terminology used in this field

        **2. Foundational Papers to Find**
        • Seminal works that this paper likely builds upon
        • Classic papers in this research area
        • Highly-cited papers in similar topics

        **3. Contemporary Research Directions**
        • Current trends in this research area
        • Recent developments and emerging topics
        • Active research groups and institutions

        **4. Search Strategy Recommendations**
        • Database search terms and boolean queries
        • Specific journals to explore
        • Conference proceedings to investigate
        • Author names to follow

        **5. Cross-Disciplinary Connections**
        • Related fields that might offer insights
        • Interdisciplinary research opportunities
        • Applications in other domains

        Format as actionable research guidance with specific suggestions.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error generating related paper suggestions: {str(e)}")
            return f"Error generating related paper suggestions: {str(e)}"
    
    def generate_research_questions(self, paper_text: str) -> str:
        """Generate potential research questions based on the paper content."""
        
        prompt = f"""
        As a research methodology expert, analyze this paper and generate meaningful research questions for future investigation:

        ❓ RESEARCH QUESTION GENERATOR:

        **1. Direct Extensions**
        • Questions that directly build on this work
        • Natural next steps for investigation
        • Unexplored parameters or variables

        **2. Methodological Questions**
        • Questions about improving the research methods
        • Alternative approaches to test the same hypothesis
        • Validation and replication studies needed

        **3. Broader Implications**
        • Questions about wider applications
        • Scalability and generalization issues
        • Real-world implementation challenges

        **4. Comparative Studies**
        • Questions comparing this approach to alternatives
        • Cross-population or cross-context studies
        • Historical or temporal comparisons

        **5. Critical Analysis Questions**
        • Questions challenging assumptions
        • Questions about limitations and edge cases
        • Questions about unintended consequences

        **6. Interdisciplinary Questions**
        • Questions connecting to other fields
        • Questions about broader societal impact
        • Questions about ethical implications

        Format each question clearly with brief rationale for why it's worth investigating.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error generating research questions: {str(e)}")
            return f"Error generating research questions: {str(e)}"
    
    def build_hypotheses(self, paper_text: str) -> str:
        """Generate new hypotheses based on the paper's findings and gaps."""
        
        prompt = f"""
        As a scientific theorist and hypothesis developer, analyze this research paper and propose new testable hypotheses:

        💡 HYPOTHESIS BUILDER:

        **1. Extension Hypotheses**
        • Hypotheses that extend current findings to new contexts
        • Predictions about scaling or generalizing results
        • Hypotheses about boundary conditions

        **2. Mechanism Hypotheses**
        • Hypotheses about underlying mechanisms not fully explored
        • Causal pathway hypotheses
        • Process improvement hypotheses

        **3. Comparative Hypotheses**
        • Hypotheses comparing different approaches or conditions
        • Hypotheses about relative effectiveness
        • Hypotheses about optimal parameters

        **4. Interaction Hypotheses**
        • Hypotheses about variable interactions not tested
        • Hypotheses about contextual moderators
        • Hypotheses about synergistic effects

        **5. Novel Application Hypotheses**
        • Hypotheses about applying findings to new domains
        • Hypotheses about cross-disciplinary applications
        • Hypotheses about practical implementations

        **6. Contradiction/Alternative Hypotheses**
        • Alternative explanations for observed phenomena
        • Hypotheses that challenge current assumptions
        • Hypotheses about conflicting findings

        Format each hypothesis as: "H: [Testable statement]" followed by brief justification and suggested testing approach.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error building hypotheses: {str(e)}")
            return f"Error building hypotheses: {str(e)}"
    
    def generate_research_proposal(self, paper_text: str) -> str:
        """Generate a research proposal based on the paper's findings and gaps."""
        
        prompt = f"""
        As a grant writing expert and research strategist, analyze this paper and draft a compelling research proposal outline:

        📋 RESEARCH PROPOSAL ASSISTANT:

        **1. EXECUTIVE SUMMARY**
        • Compelling one-paragraph summary
        • Key innovation and expected impact
        • Funding justification

        **2. RESEARCH PROBLEM & SIGNIFICANCE**
        • Clear problem statement building on this work
        • Why this research matters now
        • Knowledge gaps to be addressed
        • Potential societal/scientific impact

        **3. LITERATURE CONTEXT**
        • How this builds on current paper and related work
        • What's missing in current research
        • Positioning in the research landscape

        **4. RESEARCH OBJECTIVES & HYPOTHESES**
        • 3-5 specific, measurable objectives
        • Testable hypotheses
        • Expected outcomes and deliverables

        **5. METHODOLOGY OVERVIEW**
        • Research design approach
        • Key methods and techniques
        • Innovation in methodology
        • Validation and quality assurance

        **6. TIMELINE & MILESTONES**
        • Major phases and timeline
        • Key deliverables and milestones
        • Risk mitigation strategies

        **7. EXPECTED OUTCOMES**
        • Publications anticipated
        • Practical applications
        • Impact on field and society
        • Future research directions

        **8. BUDGET CONSIDERATIONS**
        • Major cost categories
        • Justification for resources
        • Cost-effectiveness argument

        Format as a professional research proposal outline ready for grant applications.

        PAPER TEXT:
        {paper_text[:4000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error generating research proposal: {str(e)}")
            return f"Error generating research proposal: {str(e)}"
    
    def generate_flashcards(self, content: str, num_cards: int = 15) -> str:
        """
        Generate educational flashcards from class material.
        
        Args:
            content: The educational content text
            num_cards: Number of flashcards to generate
            
        Returns:
            JSON formatted flashcards with term/definition pairs
        """
        prompt = f"""
        You are an educational content expert. Create {num_cards} high-quality flashcards from the following academic material.
        
        **FLASHCARD CREATION GUIDELINES:**
        
        **Content Focus:**
        • Key definitions and terminology
        • Important concepts and principles
        • Formulas, equations, and relationships
        • Historical figures, dates, and events
        • Process steps and methodologies
        • Cause-and-effect relationships
        
        **Format Requirements:**
        • Front: Clear, concise question or term
        • Back: Complete, accurate answer or definition
        • Use active recall principles
        • Vary question types (What is...?, How does...?, When did...?, Why does...?)
        
        **Quality Standards:**
        • One concept per card
        • No ambiguous questions
        • Include context when needed
        • Use precise academic language
        • Test understanding, not memorization
        
        Return as JSON array with this exact format:
        [
            {{"front": "Question or term", "back": "Complete answer or definition"}},
            {{"front": "Next question", "back": "Next answer"}}
        ]
        
        ACADEMIC MATERIAL:
        {content[:6000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            return f"Error generating flashcards: {str(e)}"
    
    def create_practice_questions(self, content: str, question_types: List[str] = None) -> str:
        """
        Generate practice questions from class material.
        
        Args:
            content: The educational content text
            question_types: List of question types to include
            
        Returns:
            Structured practice questions
        """
        if question_types is None:
            question_types = ["multiple_choice", "short_answer", "essay"]
            
        prompt = f"""
        You are an expert educator creating comprehensive practice questions from academic material.
        
        **QUESTION TYPES TO CREATE:**
        {', '.join(question_types)}
        
        **QUESTION GENERATION GUIDELINES:**
        
        **Multiple Choice (5 questions):**
        • Test key concepts and definitions
        • Include 4 options (A, B, C, D)
        • Make distractors plausible but clearly incorrect
        • Indicate correct answer
        
        **Short Answer (5 questions):**
        • Require 2-3 sentence explanations
        • Test understanding of processes and relationships
        • Ask for examples or applications
        • Include brief model answers
        
        **Essay Questions (3 questions):**
        • Test higher-order thinking and analysis
        • Require synthesis of multiple concepts
        • Include evaluation or comparison tasks
        • Provide key points for ideal answers
        
        **Quality Standards:**
        • Align with learning objectives
        • Various difficulty levels (basic, intermediate, advanced)
        • Clear, unambiguous wording
        • Test application, not just recall
        • Include Bloom's taxonomy levels
        
        **FORMAT:**
        ## MULTIPLE CHOICE QUESTIONS
        
        1. Question text
        A) Option 1
        B) Option 2  
        C) Option 3
        D) Option 4
        **Answer: B**
        
        ## SHORT ANSWER QUESTIONS
        
        1. Question text
        **Model Answer:** Brief explanation
        
        ## ESSAY QUESTIONS
        
        1. Question text
        **Key Points:** Main concepts to address
        
        ACADEMIC MATERIAL:
        {content[:6000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error creating practice questions: {str(e)}")
            return f"Error creating practice questions: {str(e)}"
    
    def build_study_guide(self, content: str, topic_name: str = "Academic Material") -> str:
        """
        Create a comprehensive study guide from class material.
        
        Args:
            content: The educational content text
            topic_name: Name/title of the academic topic
            
        Returns:
            Formatted study guide
        """
        prompt = f"""
        You are an expert academic tutor creating a comprehensive study guide for "{topic_name}".
        
        **STUDY GUIDE STRUCTURE:**
        
        **1. EXECUTIVE SUMMARY**
        • Main topic overview (2-3 sentences)
        • Key learning objectives
        • Why this material matters
        
        **2. KEY CONCEPTS & DEFINITIONS**
        • 10-15 most important terms with clear definitions
        • Organize by subtopic if applicable
        • Include memory aids or mnemonics where helpful
        
        **3. MAJOR THEMES & PRINCIPLES**
        • Core ideas and theories
        • Relationships between concepts
        • Underlying principles
        • Real-world applications
        
        **4. IMPORTANT DETAILS**
        • Names, dates, figures (if applicable)
        • Formulas, equations, processes
        • Examples and case studies
        • Common misconceptions to avoid
        
        **5. VISUAL LEARNING AIDS**
        • Suggest diagrams, charts, or concept maps
        • Hierarchical relationships
        • Process flows or timelines
        
        **6. QUICK REVIEW CHECKLIST**
        • "Can you explain...?" questions
        • Key points for last-minute review
        • Common exam focus areas
        
        **7. PRACTICE & APPLICATION**
        • 3 sample problems or scenarios
        • Critical thinking questions
        • Connections to other course material
        
        **8. ADDITIONAL RESOURCES**
        • Suggested supplementary readings
        • Online resources or videos
        • Study tips specific to this material
        
        **FORMATTING:**
        • Use headers, bullet points, and numbered lists
        • Make it scannable and organized
        • Include page references if applicable
        • Highlight critical information
        
        ACADEMIC MATERIAL:
        {content[:6000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            logger.error(f"Error building study guide: {str(e)}")
            return f"Error building study guide: {str(e)}"
    
    def analyze_class_material(self, content: str, material_type: str = "textbook") -> Dict[str, Any]:
        """
        Analyze class material for educational insights.
        
        Args:
            content: The educational content text
            material_type: Type of material (textbook, lecture, assignment, etc.)
            
        Returns:
            Dictionary with educational analysis
        """
        prompt = f"""
        You are an educational content analyzer. Analyze this {material_type} material and provide insights for effective studying.
        
        **ANALYSIS FRAMEWORK:**
        
        **1. CONTENT CLASSIFICATION**
        • Subject area and level (introductory, intermediate, advanced)
        • Main topics and subtopics covered
        • Prerequisite knowledge assumed
        
        **2. LEARNING OBJECTIVES**
        • What students should know after studying this
        • Skills and competencies developed
        • Assessment criteria implied
        
        **3. DIFFICULTY ASSESSMENT**
        • Overall complexity level (1-10 scale)
        • Most challenging concepts identified
        • Areas requiring extra attention
        
        **4. STUDY RECOMMENDATIONS**
        • Optimal study methods for this content type
        • Time allocation suggestions
        • Sequential vs. topic-based approach
        
        **5. KEY INSIGHTS**
        • Most important takeaways
        • Connections to broader subject
        • Practical applications
        
        **6. POTENTIAL EXAM FOCUS**
        • Likely test questions or problem types
        • Concepts that commonly appear on exams
        • Areas professors typically emphasize
        
        Provide analysis in clear, actionable format for student success.
        
        MATERIAL CONTENT:
        {content[:5000]}
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            
            # Return structured analysis
            return {
                'analysis': response.text,
                'material_type': material_type,
                'content_length': len(content),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Error analyzing class material: {str(e)}")
            return {
                'analysis': f"Error analyzing class material: {str(e)}",
                'material_type': material_type,
                'content_length': len(content),
                'generated_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }

    # New analysis methods for different document types
    def extract_key_concepts(self, content: str, document_type: str) -> str:
        """Extract key concepts from study materials."""
        prompt = f"""
        As an educational expert, identify and explain the key concepts from this study material:

        🎯 KEY CONCEPTS ANALYSIS:
        • **Core Concepts**: The fundamental ideas students must understand
        • **Supporting Concepts**: Important secondary concepts that support the main ideas
        • **Terminology**: Key terms and definitions students should memorize
        • **Relationships**: How these concepts connect to each other
        • **Examples**: Concrete examples that illustrate each concept

        Present in a clear, study-friendly format.

        CONTENT: {content[:4000]}
        """
        
        return self._make_api_call_with_retry(prompt, max_retries=5, operation_name="key concepts extraction")

    def extract_examples_cases(self, content: str, document_type: str) -> str:
        """Extract examples and case studies."""
        prompt = f"""
        As an educational content analyst, identify and organize all examples and case studies:

        💡 EXAMPLES & CASES:
        • **Real-world Examples**: Practical applications mentioned
        • **Case Studies**: Detailed scenarios or situations analyzed
        • **Illustrations**: Visual or conceptual examples used
        • **Problem Examples**: Sample problems or exercises
        • **Applications**: How concepts apply in practice

        Format for easy reference and study.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error extracting examples: {str(e)}"

    def generate_study_questions(self, content: str, document_type: str) -> str:
        """Generate study questions from content."""
        prompt = f"""
        As an educational assessment expert, create comprehensive study questions:

        ❓ STUDY QUESTIONS:
        • **Comprehension Questions**: Test basic understanding
        • **Application Questions**: Apply concepts to new situations
        • **Analysis Questions**: Break down complex ideas
        • **Synthesis Questions**: Combine multiple concepts
        • **Critical Thinking**: Evaluate and compare ideas

        Include a mix of multiple choice, short answer, and essay questions.

        CONTENT: {content[:4000]}
        """
        
        return self._make_api_call_with_retry(prompt, max_retries=5, operation_name="study questions generation")

    def assess_difficulty(self, content: str, document_type: str) -> str:
        """Assess the difficulty level of content."""
        prompt = f"""
        As an educational psychologist, assess the difficulty level of this content:

        📊 DIFFICULTY ASSESSMENT:
        • **Overall Difficulty**: Rate 1-10 with justification
        • **Prerequisite Knowledge**: What background is needed?
        • **Complex Areas**: Which sections are most challenging?
        • **Time Investment**: How much study time is recommended?
        • **Study Strategies**: Best approaches for this difficulty level

        Provide practical guidance for students.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error assessing difficulty: {str(e)}"

    def analyze_structure(self, content: str, document_type: str) -> str:
        """Analyze document structure."""
        prompt = f"""
        As a document analysis expert, analyze the structure and organization:

        🏗️ STRUCTURE ANALYSIS:
        • **Overall Organization**: How is content structured?
        • **Logical Flow**: Does the sequence make sense?
        • **Section Breakdown**: Main sections and their purposes
        • **Transitions**: How sections connect
        • **Effectiveness**: How well does structure support learning?

        Focus on how structure aids comprehension.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error analyzing structure: {str(e)}"

    def analyze_arguments(self, content: str, document_type: str) -> str:
        """Analyze key arguments presented."""
        prompt = f"""
        As an argumentation expert, identify and analyze the key arguments:

        💭 ARGUMENT ANALYSIS:
        • **Main Arguments**: Primary claims being made
        • **Supporting Evidence**: Evidence provided for each argument
        • **Logical Structure**: How arguments are constructed
        • **Counterarguments**: Alternative viewpoints addressed
        • **Strength Assessment**: Evaluate argument quality

        Focus on logical reasoning and evidence quality.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error analyzing arguments: {str(e)}"

    def suggest_improvements(self, content: str, document_type: str) -> str:
        """Suggest improvements for academic work."""
        prompt = f"""
        As an academic writing coach, suggest constructive improvements:

        ✨ IMPROVEMENT SUGGESTIONS:
        • **Content Clarity**: Ways to make ideas clearer
        • **Structure Enhancement**: Organizational improvements
        • **Evidence Strengthening**: Better support for claims
        • **Writing Style**: Clarity and engagement improvements
        • **Academic Standards**: Meeting academic expectations

        Provide specific, actionable suggestions.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error suggesting improvements: {str(e)}"

    def extract_findings(self, content: str, document_type: str) -> str:
        """Extract key findings from reports/documents."""
        prompt = f"""
        As a research analyst, identify and summarize key findings:

        📈 KEY FINDINGS:
        • **Primary Findings**: Most important discoveries or results
        • **Secondary Findings**: Supporting observations
        • **Data Insights**: What the data reveals
        • **Patterns**: Trends or patterns identified
        • **Significance**: Why these findings matter

        Present in clear, prioritized format.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error extracting findings: {str(e)}"

    def extract_recommendations(self, content: str, document_type: str) -> str:
        """Extract recommendations from documents."""
        prompt = f"""
        As a policy analyst, identify and organize all recommendations:

        💡 RECOMMENDATIONS:
        • **Primary Recommendations**: Main suggested actions
        • **Implementation Steps**: How to execute recommendations
        • **Priority Level**: Which recommendations are most important
        • **Target Audience**: Who should act on these recommendations
        • **Expected Outcomes**: What results are anticipated

        Focus on actionable guidance.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error extracting recommendations: {str(e)}"

    def extract_main_points(self, content: str, document_type: str) -> str:
        """Extract main points from any academic content."""
        prompt = f"""
        As a content analyst, identify and organize the main points:

        🎯 MAIN POINTS:
        • **Central Ideas**: The core messages or themes
        • **Supporting Points**: Important details that support main ideas
        • **Key Takeaways**: What readers should remember
        • **Action Items**: Any suggested actions or next steps
        • **Priority Ranking**: Order of importance

        Present in a clear, hierarchical format.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error extracting main points: {str(e)}"

    def analyze_context(self, content: str, document_type: str) -> str:
        """Analyze the context and background."""
        prompt = f"""
        As a contextual analyst, provide background and situational context:

        🌍 CONTEXT ANALYSIS:
        • **Historical Context**: When and why was this created?
        • **Field/Domain**: What academic or professional field?
        • **Intended Audience**: Who is the target reader?
        • **Purpose**: Why was this document created?
        • **Broader Significance**: How does this fit into larger conversations?

        Help readers understand the bigger picture.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error analyzing context: {str(e)}"

    def suggest_future_research(self, content: str) -> str:
        """Suggest future research directions."""
        prompt = f"""
        As a research strategist, suggest future research directions:

        🔮 FUTURE RESEARCH DIRECTIONS:
        • **Immediate Next Steps**: Short-term research opportunities
        • **Long-term Investigations**: Major research programs needed
        • **Interdisciplinary Connections**: Other fields to involve
        • **Methodological Advances**: New approaches to try
        • **Practical Applications**: Real-world implementation studies

        Focus on feasible and impactful research directions.

        CONTENT: {content[:4000]}
        """
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error suggesting future research: {str(e)}"

    def extract_citations(self, content: str, document_type: str = "🔬 Research Paper") -> str:
        """Extract citations and references based on document type."""
        if "Research Paper" in document_type:
            prompt = f"""
            As a bibliography expert, extract and analyze citations:

            📚 CITATIONS & REFERENCES:
            • **Key References**: Most important sources cited
            • **Reference Types**: Books, journals, websites, etc.
            • **Citation Quality**: Credibility and relevance assessment
            • **Research Lineage**: How this builds on previous work
            • **Missing References**: Potential sources that should be included

            Focus on the scholarly foundation of this work.
            """
        else:
            prompt = f"""
            As a reference analyst, identify sources and references:

            📚 REFERENCES & SOURCES:
            • **Primary Sources**: Original materials referenced
            • **Supporting Materials**: Additional resources mentioned
            • **Credibility Assessment**: Quality of sources used
            • **Further Reading**: Related materials for deeper study
            • **Source Types**: Books, articles, websites, etc.

            Help readers understand the information foundation.
            """
        
        prompt += f"\n\nCONTENT: {content[:4000]}"
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error extracting references: {str(e)}"

    def extract_keywords(self, content: str, document_type: str = "🔬 Research Paper") -> str:
        """Extract keywords and key terms based on document type."""
        if "Research Paper" in document_type:
            prompt = f"""
            As a domain expert, extract research terminology:

            🏷️ RESEARCH KEYWORDS:
            • **Primary Keywords**: Core research terms
            • **Technical Terminology**: Specialized vocabulary
            • **Theoretical Concepts**: Key theoretical terms
            • **Methodological Terms**: Research method vocabulary
            • **Field-Specific Language**: Discipline-specific terms

            Focus on terms crucial for research and academic discourse.
            """
        else:
            prompt = f"""
            As an educational vocabulary expert, extract key terms:

            🏷️ KEY TERMS & VOCABULARY:
            • **Essential Terms**: Must-know vocabulary
            • **Concept Names**: Important concept labels
            • **Technical Terms**: Specialized vocabulary explained
            • **Study Terms**: Terms students should memorize
            • **Context Clues**: How terms are used in context

            Focus on vocabulary important for learning and comprehension.
            """
        
        prompt += f"\n\nCONTENT: {content[:4000]}"
        
        try:
            response = self.model.generate_content(prompt, generation_config=self.generation_config)
            return response.text
        except Exception as e:
            return f"Error extracting keywords: {str(e)}"

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