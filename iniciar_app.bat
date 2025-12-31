@echo off
cd /d C:\Users\pauli\controle_docs_app
call .\.venv\Scripts\activate
streamlit run app.py
pause