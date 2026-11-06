@echo off
cd /d "%~dp0"
where py >nul 2>nul || (echo Python 3.10+ is required. & pause & exit /b 1)
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-local.txt
python -m streamlit run streamlit_app.py
pause
