@echo off
REM Quick diagnostic for resume system health
cd /d "%~dp0"

echo.
echo ============================================================
echo  Resume System Diagnostic
echo ============================================================
echo.

python diagnose_resumes.py

pause
