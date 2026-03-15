@echo off
echo Starting Sensor Simulator...
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
