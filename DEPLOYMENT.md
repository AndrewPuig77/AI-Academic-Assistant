# 🚀 Deployment Guide - Streamlit Community Cloud

This guide will help you deploy the AI Research Paper Analyst to Streamlit Community Cloud.

## 📋 Prerequisites

1. **GitHub Repository**: Your code must be in a public GitHub repository
2. **Google Gemini API Key**: Get one from [Google AI Studio](https://aistudio.google.com/app/apikey)
3. **Streamlit Community Cloud Account**: Sign up at [share.streamlit.io](https://share.streamlit.io)

## 🛠️ Deployment Steps

### Step 1: Prepare Your Repository

1. **Fork or Clone**: Make sure your code is in a GitHub repository
2. **Check Files**: Ensure these files are present:
   - `main.py` (main application file)
   - `requirements.txt` (dependencies)
   - `.streamlit/config.toml` (Streamlit configuration)
   - `app/` directory with all modules

### Step 2: Deploy to Streamlit Cloud

1. **Visit Streamlit Cloud**: Go to [share.streamlit.io](https://share.streamlit.io)
2. **Sign In**: Use your GitHub account to sign in
3. **Create New App**: Click "New app"
4. **Configure Deployment**:
   - **Repository**: Select your repository (`AndrewPuig77/AI-Research-Paper-analyst`)
   - **Branch**: `main`
   - **Main file path**: `main.py`
   - **App URL**: Choose a custom URL (e.g., `ai-research-analyst`)

### Step 3: Configure Secrets

1. **In Streamlit Cloud Dashboard**: Go to your app settings
2. **Secrets Tab**: Add your environment variables:

```toml
# Add this to your Streamlit Cloud secrets
GOOGLE_API_KEY = "your_actual_api_key_here"
APP_NAME = "AI Research Paper Assistant"
DEBUG = false
MAX_UPLOAD_SIZE = 10485760
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_TEMPERATURE = 0.1
GEMINI_MAX_TOKENS = 8192
```

### Step 4: Deploy

1. **Click Deploy**: Streamlit will automatically build and deploy your app
2. **Monitor Logs**: Watch the deployment logs for any errors
3. **Access Your App**: Once deployed, you'll get a public URL

## 🔧 Configuration Details

### Requirements.txt
Your app uses these key dependencies:
- `streamlit==1.50.0`
- `google-generativeai==0.8.5`
- `PyMuPDF==1.26.4` (PDF processing)
- `pandas`, `matplotlib`, `plotly` (data visualization)

### Streamlit Config
The `.streamlit/config.toml` file sets:
- Dark theme to match your custom styling
- Optimal server settings for cloud deployment
- Privacy settings (no usage stats collection)

## 🚨 Important Security Notes

1. **Never commit API keys**: Your `.env` file is ignored by git
2. **Use Streamlit Secrets**: For production, always use Streamlit Cloud's secrets management
3. **API Key Safety**: Your Google API key should never appear in your code

## 📊 Resource Limits

**Streamlit Community Cloud Limits:**
- **Memory**: 1 GB RAM
- **CPU**: Shared CPU resources
- **Storage**: Limited temporary storage
- **Bandwidth**: Fair usage policy
- **Apps**: Up to 3 public apps per user

## 🛠️ Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **API Key Errors**: Verify your Google API key is correctly set in secrets
3. **Memory Issues**: Large PDF files might cause memory problems
4. **Timeout Issues**: Complex analysis might exceed time limits

### Solutions:

1. **Optimize Dependencies**: Remove unused packages from requirements.txt
2. **Error Handling**: The app has built-in error handling for API issues
3. **File Size Limits**: App limits uploads to 10MB
4. **Model Fallback**: App automatically tries different Gemini models if one fails

## 🎯 Production Optimizations

Your app is already optimized for production with:
- ✅ Automatic model selection (tries multiple Gemini models)
- ✅ Error handling and user feedback
- ✅ File size validation (10MB limit)
- ✅ Memory-efficient PDF processing
- ✅ Rate limiting between API calls
- ✅ Dark theme for better performance

## 📈 Monitoring

Once deployed, you can monitor your app through:
- **Streamlit Cloud Dashboard**: View logs, metrics, and manage settings
- **Google AI Studio**: Monitor API usage and quotas
- **App Analytics**: Track usage patterns (if enabled)

## 🔄 Updates

To update your deployed app:
1. **Push to GitHub**: Commit changes to your main branch
2. **Auto-Deploy**: Streamlit Cloud automatically detects changes and redeploys
3. **Manual Reboot**: You can manually restart the app from the dashboard if needed

Your AI Research Paper Analyst is now ready for public deployment! 🚀