@echo off
REM Daily collector: scrapes DGFT from your Indian connection, stores AI summaries in Supabase.
cd /d "%~dp0src"
echo ===== %date% %time% ===== >> "%~dp0collect.log"
python run_daily.py >> "%~dp0collect.log" 2>&1
