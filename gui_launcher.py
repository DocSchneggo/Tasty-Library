#!/usr/bin/env python3
"""
Launcher script for Tasty Library GUI
Run this script to start the PyQt6 GUI application
"""

import sys
import os

# Add the project directory to the path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

try:
    from gui import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print("Error: Required dependencies not found!")
    print(f"Details: {e}")
    print("\nPlease install PyQt6 using:")
    print("  pip install PyQt6")
    sys.exit(1)
except Exception as e:
    print(f"Error starting GUI: {e}")
    sys.exit(1)
