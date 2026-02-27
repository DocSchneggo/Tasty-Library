@echo off
REM Tasty Library GUI Launcher for Windows

REM Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found!
    echo Please create one using: python -m venv .venv
    pause
    exit /b 1
)

REM Check if PyQt6 is installed
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo PyQt6 not found. Installing...
    pip install PyQt6
    if errorlevel 1 (
        echo Failed to install PyQt6
        pause
        exit /b 1
    )
)

REM Start the GUI
echo Starting Tasty Library GUI...
python gui_launcher.py
pause
