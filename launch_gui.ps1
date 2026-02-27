# Tasty Library GUI Launcher for PowerShell

# Check if virtual environment exists
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..."
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create one using: python -m venv .venv"
    exit 1
}

# Check if PyQt6 is installed
try {
    python -c "import PyQt6" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "PyQt6 not found"
    }
} catch {
    Write-Host "PyQt6 not found. Installing..." -ForegroundColor Yellow
    pip install PyQt6
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install PyQt6" -ForegroundColor Red
        exit 1
    }
}

# Start the GUI
Write-Host "Starting Tasty Library GUI..." -ForegroundColor Green
python gui_launcher.py
