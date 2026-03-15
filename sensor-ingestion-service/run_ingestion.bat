@echo off
echo Starting Sensor Ingestion Service...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
set RABBITMQ_HOST=localhost
set DATA_STORAGE_URL=http://localhost:8003
uvicorn main:app --host 0.0.0.0 --port 8004
