@echo off
REM MkweliAML Windows Runner

REM Activate venv if exists
IF EXIST venv\Scripts\activate.bat (
    CALL venv\Scripts\activate.bat
)

python app.py
pause
