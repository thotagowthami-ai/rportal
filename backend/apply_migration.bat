@echo off
REM Migration script for recruiting platform backend
cd /d "%~dp0"

echo Applying database migration...
python apply_migration.py

if %errorlevel% equ 0 (
    echo.
    echo Migration completed successfully!
    echo You can now start the backend with: python -m uvicorn app.main:app --reload
) else (
    echo.
    echo Migration failed! Check the error message above.
)

pause
