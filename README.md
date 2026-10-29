# AI Academic Assistant

[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Google Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-4285F4?logo=google&logoColor=white)](https://ai.google.dev/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An AI-powered web application that turns research papers and course materials into structured analysis and study resources. Upload a document and receive executive summaries, methodology reviews, citation analysis, flashcards, practice questions, and study guides — generated with Google Gemini by default, or with OpenAI, Anthropic Claude, or any OpenAI-compatible model using your own API key.

**[Live Demo →](https://ai-academic-assistant-o6pz88nwe9q4zspiioe3nc.streamlit.app/)**

---

## Table of Contents

- [Features](#features)
- [Getting Started](#getting-started)
- [AI Providers](#ai-providers)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technology Stack](#technology-stack)
- [Deployment](#deployment)
- [License](#license)

---

## Features

### Research Analysis

| Feature | Description |
| --- | --- |
| **Document Processing** | Text extraction from PDF, DOCX, and TXT files with structure preservation |
| **Executive Summary** | Concise, accessible overview of the paper's contributions |
| **Methodology Review** | Detailed breakdown of research design, methods, and procedures |
| **Citation Analysis** | Reference extraction and citation network visualization |
| **Research Gap Identification** | Highlights open questions and unexplored directions |
| **Keyword Extraction** | Key terms, concepts, and technical vocabulary |
| **Related Paper Suggestions** | Recommendations for further reading |
| **Research Question Generator** | Proposes questions for future investigation |
| **Hypothesis Builder** | Develops testable hypotheses from the paper's findings |
| **Proposal Assistant** | Drafts research proposals and grant application outlines |

### Study Tools

| Feature | Description |
| --- | --- |
| **Flashcards** | Key definitions and concepts formatted for active recall |
| **Practice Questions** | Multiple-choice, short-answer, and essay questions |
| **Study Guides** | Topic-organized guides with summaries |
| **Material Analysis** | Difficulty assessment and study recommendations |
| **Exam Focus** | Identifies the concepts most likely to be tested |
| **Export** | Download individual resources or a complete study package |

---

## Getting Started

### Prerequisites

- Python 3.10 or later
- A Google Gemini API key — [create one in Google AI Studio](https://aistudio.google.com/app/apikey) (free tier available). Optional if users will bring their own key for another provider.

### Installation

```bash
# Clone the repository
git clone https://github.com/AndrewPuig77/AI-Academic-Assistant.git
cd AI-Academic-Assistant

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Create your environment file
cp .env.example .env             # macOS / Linux
copy .env.example .env           # Windows
```

### Running the Application

```bash
streamlit run main.py
```

The app will be available at **http://localhost:8501**.

Windows users can alternatively run `run_app.bat`.

---

## AI Providers

Choose the AI provider in the app's sidebar. Gemini is the default.

| Provider | Default model | Key |
| --- | --- | --- |
| Google Gemini | `gemini-flash-latest` (falls back automatically if a model is retired) | Built-in `GOOGLE_API_KEY`, or the user's own |
| OpenAI | `gpt-5-mini` | User's own, or built-in `OPENAI_API_KEY` |
| Anthropic Claude | `claude-opus-5-5` | User's own, or built-in `ANTHROPIC_API_KEY` |
| OpenAI-compatible | Any model on the server | Optional — for Groq, OpenRouter, Together, Ollama, LM Studio, and similar |

Users can override the model name in the sidebar. Keys entered in the app are kept only for the browser session and are never saved. If a user leaves the key blank, the app uses the host's built-in key for that provider when one is configured.

---

## Configuration

Settings are read from a `.env` file in the project root (or Streamlit secrets when deployed). Set the built-in Gemini key:

```env
GOOGLE_API_KEY=your_api_key_here
```

| Variable | Default | Description |
| --- | --- | --- |
| `GOOGLE_API_KEY` | — | Built-in Google Gemini key for the default provider |
| `OPENAI_API_KEY` | — | Optional built-in OpenAI key |
| `ANTHROPIC_API_KEY` | — | Optional built-in Anthropic key |
| `GEMINI_MODEL` | `gemini-flash-latest` | Preferred Gemini model |
| `GEMINI_TEMPERATURE` | `0.1` | Sampling temperature for generated output |
| `GEMINI_MAX_TOKENS` | `8192` | Maximum tokens per response |

See [`.env.example`](.env.example) for the full template.

---

## Usage

### Analyzing a Research Paper

1. **Upload** a paper (PDF, DOCX, or TXT).
2. **Select** the analyses you want — summary, methodology, citations, and more.
3. **Explore** the research tools to generate questions, hypotheses, or a proposal draft.
4. **Export** the results as a text or JSON report.

### Creating Study Materials

1. **Upload** lecture notes, textbook chapters, or course handouts.
2. **Choose** flashcards, practice questions, or a study guide.
3. **Review** the difficulty assessment and study recommendations.
4. **Download** individual resources or the complete study package.

### Example Output

*Research analysis — "Attention Is All You Need":*

```
EXECUTIVE SUMMARY
This paper introduces the Transformer architecture, which relies entirely on
attention mechanisms and dispenses with recurrence and convolutions...

GENERATED HYPOTHESES
1. Transformer architectures can be adapted to computer vision tasks.
2. Attention mechanisms may improve other sequence modeling problems.
```

*Study materials — introductory machine learning chapter:*

```
FLASHCARD
Front: What is supervised learning?
Back:  A paradigm in which models learn from labeled training data...

PRACTICE QUESTION
Which model is best suited to classification with non-linear boundaries?
A) Linear Regression  B) Decision Trees  C) SVM with RBF kernel  D) All of the above
```

---

## Project Structure

```
AI-Academic-Assistant/
├── main.py                     # Streamlit application entry point
├── app/
│   ├── core/
│   │   ├── document_processor.py   # PDF / DOCX / TXT ingestion
│   │   ├── pdf_processor.py        # PDF text extraction (PyMuPDF)
│   │   ├── gemini_analyzer.py      # Analysis prompts and logic (all providers)
│   │   └── providers/              # Gemini, OpenAI, Claude, and OpenAI-compatible adapters
│   └── utils/
│       ├── helpers.py              # Shared utilities
│       └── report_generator.py     # Report building and export
├── .streamlit/                 # Streamlit configuration
├── .env.example                # Environment variable template
├── requirements.txt
└── DEPLOYMENT.md               # Deployment guide
```

---

## Technology Stack

| Layer | Tools |
| --- | --- |
| Interface | [Streamlit](https://streamlit.io/) |
| AI Models | [Google Gemini](https://ai.google.dev/) (`google-genai`), [OpenAI](https://platform.openai.com/) (`openai`), [Anthropic Claude](https://platform.claude.com/) (`anthropic`) |
| Document Processing | PyMuPDF, python-docx, chardet |
| Visualization | Plotly, Matplotlib, Seaborn, NetworkX, WordCloud |
| Reporting | ReportLab, pandas |

---

## Deployment

The application is deployed on Streamlit Community Cloud. For instructions on deploying your own instance, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
