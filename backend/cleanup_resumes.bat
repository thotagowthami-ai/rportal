@echo off
REM Cleanup script for missing resume files
cd /d "%~dp0"

echo.
echo ============================================================
echo  Resume Cleanup Utility
echo ============================================================
echo.

if "%1"=="--cleanup" (
    echo Running cleanup...
    python cleanup_resumes.py --cleanup
) else (
    echo Scanning for missing resume files...
    python cleanup_resumes.py
    echo.
    echo To cleanup missing resumes, run:
    echo   cleanup_resumes.bat --cleanup
)

pause
