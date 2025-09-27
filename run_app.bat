@echo off
echo ====================================
echo   AI Research Paper Assistant
echo   Powered by Google Gemini AI
echo ====================================
echo.

echo Checking environment...
if not exist ".venv\Scripts\python.exe" (
    echo Error: Virtual environment not found!
    echo Please run setup first.
    pause
    exit /b 1
)

echo Starting Streamlit application...
echo.
echo Open your browser to: http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

.venv\Scripts\python.exe -m streamlit run main.py

pause