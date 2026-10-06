@echo off
REM Quality check: AI auditor re-reads 10 random official PDFs and checks the summaries.
cd /d "%~dp0src"
python qa.py
pause
