@echo off
echo Starting Data Storage Service...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8003
