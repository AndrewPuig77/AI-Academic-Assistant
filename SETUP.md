# 🚀 Quick Setup Guide

## Step 1: Get Your Google API Key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy the API key

## Step 2: Configure the Application
1. Open the `.env` file in your project folder
2. Replace `your_google_api_key_here` with your actual API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

## Step 3: Run the Application
- **Windows**: Double-click `run_app.bat`
- **Manual**: Run `streamlit run main.py` in your terminal

## Step 4: Use the Application
1. Open http://localhost:8501 in your browser
2. Upload a PDF research paper
3. Choose analysis options
4. Click "Analyze Paper"
5. View results in the Results tab

## 📝 Tips for Best Results
- Use academic research papers (not books or reports)
- PDFs should be text-based (not scanned images)
- Papers up to 10MB are supported
- Clear, well-structured papers work best

## 🔧 Troubleshooting
- **API Key Error**: Make sure your .env file has the correct API key
- **PDF Error**: Ensure your PDF is text-based and under 10MB
- **Slow Analysis**: Large papers take longer to process
- **Port Error**: Try running on a different port: `streamlit run main.py --server.port 8502`

## 🎯 Demo Papers
For testing, try papers from:
- [arXiv.org](https://arxiv.org/)
- [Google Scholar](https://scholar.google.com/)
- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)

Look for papers in PDF format that are 10-20 pages long for best demo results!