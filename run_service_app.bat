@echo off
echo ============================================
echo  SE Service Campaign - Spring 2026
echo  Seasonal Customer Targeting (Mar/Apr/May)
echo ============================================
echo.
cd /d "%~dp0"
echo Installing requirements...
pip install -r service_requirements.txt -q
echo.
echo Starting app on http://localhost:8502
echo.
streamlit run service_app.py --server.port 8502
pause
