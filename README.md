# 🎓 Academic AI Assistant

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF6B6B)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-4285F4)](https://ai.google.dev/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB)](https://python.org/)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Transform research papers AND class materials into actionable insights with cutting-edge AI analysis. Perfect for researchers, students, and academics who need comprehensive document analysis and study tools.

![Academic AI Assistant Demo](https://via.placeholder.com/800x400/1f77b4/ffffff?text=Academic+AI+Assistant)

## ✨ Dual-Purpose Features

### 🔬 **Research Analysis Tools**
Transform dense research papers into comprehensive insights:

- **📄 Smart PDF Processing** - Advanced text extraction with structure preservation
- **📝 Executive Summaries** - Concise, accessible overviews of complex research  
- **🔬 Methodology Breakdown** - Deep-dive analysis of research methods and procedures
- **📚 Citation Network Analysis** - Automatic reference extraction and relationship mapping
- **🔍 Research Gap Identification** - AI-powered discovery of unexplored opportunities
- **🏷️ Keyword Extraction** - Key terms, concepts, and technical vocabulary
- **� Related Paper Suggestions** - AI-powered discovery of similar research
- **❓ Research Question Generator** - Generate meaningful questions for future investigation
- **💡 Hypothesis Builder** - Develop testable hypotheses from research findings
- **📋 Research Proposal Assistant** - AI-guided proposal drafting and grant applications

### 📚 **Student Study Tools** 
Turn class materials into effective study resources:

- **📇 Smart Flashcards** - Extract key definitions and concepts for active recall
- **❓ Practice Questions** - Generate multiple choice, short answer, and essay questions
- **📖 Study Guides** - Create comprehensive guides with organized topics and summaries
- **📊 Material Analysis** - Assess difficulty levels and provide study recommendations
- **⏰ Exam Focus Predictions** - Identify likely test areas and important concepts
- **💾 Export Everything** - Download all study materials as formatted files

## 🎯 **Perfect For**

### 🎓 **Researchers & Academics**
- Quickly understand complex papers in your field
- Generate research ideas and hypotheses
- Draft compelling research proposals
- Identify gaps in current literature

### 📚 **Students** 
- Break down difficult textbooks and course materials
- Create effective study materials (flashcards, guides, questions)
- Prepare for exams with AI-generated practice questions
- Understand complex academic papers for assignments

### 🔬 **Research Teams**
- Streamline literature review processes
- Collaborative analysis and discussion
- Stay updated with latest developments
- Generate new research directions

### � **Educators**
- Quickly analyze teaching materials
- Create study resources for students
- Develop comprehensive course content
- Assess material difficulty and learning objectives

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

```bash
# Clone the repository
git clone https://github.com/AndrewPuig77/AI-Research-Paper-analyst.git
cd AI-Research-Paper-analyst

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and add your Google API key
```

### Configuration

1. **Get Your Google Gemini API Key**
   - Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a new API key (FREE tier available!)
   - Copy the key

2. **Configure the Application**
   ```bash
   # Edit the .env file
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

### Run the Application

```bash
# Start the Streamlit app
streamlit run main.py
```

Open your browser to **http://localhost:8501** and start analyzing! 🎉

## 📖 Usage

### For Research Papers
1. **📤 Upload** - Drop a research paper PDF
2. **⚙️ Configure** - Select analysis options (summary, methodology, citations, etc.)
3. **🔬 Research Tools** - Generate questions, hypotheses, and research proposals
4. **📥 Export** - Download comprehensive analysis reports

### For Class Materials  
1. **� Upload** - Drop textbook chapters, lecture notes, or course handouts
2. **📚 Study Tools** - Choose flashcards, practice questions, or study guides
3. **� Analyze** - Get difficulty assessments and study recommendations
4. **� Export** - Download complete study packages

## 🛠️ Technology Stack

### Core Technologies
- **🐍 Python 3.11+** - Modern Python with advanced features
- **🎨 Streamlit** - Beautiful, interactive web interface with modern black theme
- **🤖 Google Gemini 2.5/2.0** - State-of-the-art AI for analysis (FREE tier: 1,500 requests/day!)
- **📄 PyMuPDF** - Advanced PDF processing and text extraction
- **� Plotly, Matplotlib, Seaborn** - Interactive visualizations and charts
- **☁️ WordCloud** - Visual text analysis and keyword representation
- **� ReportLab** - PDF export functionality

### FREE Tier Benefits
- **✨ Gemini 2.5 Flash**: 1,500 requests per day
- **🧠 Gemini 2.0 Pro**: 100 requests per day
- **� Analysis Capacity**: Analyze 250-500 documents daily!
- **⏰ Reset**: Quota resets daily at midnight UTC

## 🎯 Demo Examples

### Research Paper Analysis
**Paper**: "Attention Is All You Need" (Transformer Architecture)

```
📝 EXECUTIVE SUMMARY
This groundbreaking paper introduces the Transformer architecture, 
revolutionizing NLP by relying entirely on attention mechanisms...

🔬 METHODOLOGY ANALYSIS  
Research Design: Experimental study with novel neural architecture
Strength: 5/5 - Rigorous experimental setup with comprehensive baselines...

💡 GENERATED HYPOTHESES
1. Transformer architecture can be adapted for computer vision tasks
2. Attention mechanisms might improve other sequence modeling problems...
```

### Study Material Creation
**Material**: "Introduction to Machine Learning" (Textbook Chapter)

```
📇 FLASHCARDS GENERATED (15 cards)
Front: What is supervised learning?
Back: A machine learning paradigm where algorithms learn from labeled training data...

❓ PRACTICE QUESTIONS
Multiple Choice: Which algorithm is best for classification tasks with non-linear boundaries?
A) Linear Regression B) Decision Trees C) SVM with RBF kernel D) All of the above
**Answer: C**

📖 STUDY GUIDE
KEY CONCEPTS: Supervised vs Unsupervised Learning, Training/Validation Split...
EXAM FOCUS: Likely to test algorithm selection and evaluation metrics...
```

## 🏗️ Project Structure

```
academic-ai-assistant/
├── 📁 app/
│   ├── 🔧 core/
│   │   ├── pdf_processor.py      # PDF text extraction & processing
│   │   ├── gemini_analyzer.py    # Gemini AI integration with study tools
│   │   └── __init__.py
│   ├── 🛠️ utils/
│   │   ├── helpers.py            # Utility functions
│   │   ├── report_generator.py   # Advanced report generation
│   │   └── __init__.py
│   └── __init__.py
├── 📁 uploads/                   # Temporary file storage  
├── 🎨 main.py                   # Streamlit main application (5 tabs!)
├── ⚙️ requirements.txt          # Python dependencies
├── 🔧 .env.example              # Environment template
└── 📖 README.md                 # This file
```

## 🚀 Roadmap

### ✅ Current Features (v2.0)
- ✅ Research Paper Analysis with AI Insights
- ✅ Student Study Tools (Flashcards, Questions, Guides) 
- ✅ Modern Black Theme Interface
- ✅ Export Functionality for All Materials
- ✅ Advanced AI Research Assistant Features

### 🎯 Coming Soon (v2.1)
- 🔄 Multi-Document Comparison
- 📊 Visual Knowledge Graphs
- 📱 Mobile-Responsive Design
- 🌐 Multi-Language Support

##  License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **🤖 Google Gemini** - For providing powerful FREE AI capabilities
- **🎨 Streamlit** - For the amazing web framework
- **📄 PyMuPDF** - For robust PDF processing
- **🎓 Academic Community** - For inspiring this comprehensive tool

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/AndrewPuig77/AI-Research-Paper-analyst/issues)
- 💬 **Discussions**: Create discussions for feature requests
- � **Contact**: Questions about implementation or customization

## ⭐ Show Your Support

If this project helped you with your research or studies:
- ⭐ **Star** this repository
- 🍴 **Fork** for your own modifications  
- 📢 **Share** with fellow researchers and students
- 💝 **Contribute** to make it even better

---

<div align="center">
  <p><strong>Built with ❤️ for researchers AND students</strong></p>
  <p><em>Making academic success accessible to everyone</em></p>
  
  ![Made with Love](https://img.shields.io/badge/Made%20with-❤️-red.svg)
  ![Open Source](https://img.shields.io/badge/Open%20Source-💚-brightgreen.svg)
  ![Student Friendly](https://img.shields.io/badge/Student-Friendly-blue.svg)
</div>
