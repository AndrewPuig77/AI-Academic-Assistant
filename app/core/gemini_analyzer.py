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