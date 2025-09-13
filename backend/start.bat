@echo off
REM change working directory to project root (parent of this .bat file)
cd /d %~dp0\..
REM ensure project root is on PYTHONPATH
set PYTHONPATH=%CD%
REM run uvicorn with package path so imports like `from backend...` work
py -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
