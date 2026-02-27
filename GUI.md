# Tasty Library GUI - User Guide

A professional PyQt6-based graphical interface for the Tasty Library management system.

## Installation

### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

### Setup

1. **Install PyQt6** (if not already installed):
   ```bash
   pip install PyQt6
   ```

2. **Or install all dependencies** (if requirements.txt exists):
   ```bash
   pip install -r requirements.txt
   ```

## Launching the GUI

### Option 1: Windows Batch File (Easiest)
Double-click `launch_gui.bat` to start the GUI. This will:
- Activate your virtual environment
- Install PyQt6 if needed
- Launch the application

### Option 2: PowerShell
Run the following in PowerShell:
```powershell
.\launch_gui.ps1
```

### Option 3: Python
```bash
python gui_launcher.py
```

## Features

### 1. **Database Connection**
- **Connect to Database**: File → Connect to Database
- Select your `.db` database file to connect
- Status bar shows the connected database

### 2. **Users Management Tab**
Manage library users with full CRUD operations:

#### Add User
- Click "Add User" button
- Enter username
- Select status: Active, Inactive, or Banned
- Click "Add"

#### Remove User
- Select a user from the table
- Click "Remove Selected"
- Confirm the deletion

#### View Users
- Table displays:
  - User ID
  - Username
  - Status (Active/Inactive/Banned)
  - Creation date

### 3. **Books Management Tab**
Manage your library's book collection:

#### Add Book
- Click "Add Book" button
- Fill in:
  - **Title** (required)
  - **Author** (required)
  - **ISBN** (required)
  - **Description** (optional)
- Click "Add"

#### Remove Book
- Select a book from the table
- Click "Remove Selected"
- Confirm the deletion

#### View Books
- Table displays:
  - Book ID
  - Title
  - Author
  - ISBN
  - Borrowed by (user name or "Available")
  - Description

### 4. **Borrowing Management Tab**
Track and manage book loans:

#### Borrow a Book
- Click "Borrow Book" button
- Select:
  - **Book**: Available books only shown
  - **User**: Select the borrower
  - **Return Date**: Default is 30 days from today
- Click "Borrow"

#### Return a Book
- View active borrows in the table
- Select a borrowed book
- Click "Return Selected"
- Confirm the return

#### View Active Borrows
- Table displays:
  - Borrow ID
  - Book Title
  - Borrower Name
  - Borrowed Date
  - Return Date
  - Delayed Status

## Database Requirements

Your database must have the following tables:
- `users`: id, name, state, created_at
- `books`: id, title, author, isbn, borrowed_by, borrowed_at, description
- `borrows`: id, book_id, borrower_id, created_at, return_date, renewed, delayed

See `sql/create_tables.sql` for the full schema.

## Files

- `gui.py` - Main GUI application code
- `gui_launcher.py` - Python launcher script
- `launch_gui.bat` - Windows batch launcher
- `launch_gui.ps1` - PowerShell launcher
- `GUI.md` - This documentation

## Keyboard Shortcuts

- `Ctrl+Q` - Exit application
- `Tab` - Navigate between fields in dialogs
- `Enter` - Confirm action

## Troubleshooting

### PyQt6 Import Error
If you see "No module named 'PyQt6'":
```bash
pip install PyQt6
```

### Database Connection Failed
- Ensure the database file exists
- Check file permissions
- Verify the database has required tables

### GUI Won't Start
- Ensure Python 3.8+ is installed
- Check that all dependencies are installed
- Try running from command line to see error messages

## Architecture

The GUI consists of:
- **LibraryManager**: Backend database operations
- **Dialog Classes**: AddUserDialog, AddBookDialog, BorrowDialog
- **TastyLibraryGUI**: Main window with tabs for Users, Books, and Borrowing
- **Tab Widgets**: Specialized UI for each functionality area

## Future Enhancements

Possible features to add:
- Search and filter functionality
- Export/import user and book data
- Statistics/reports dashboard
- Book cover images
- User profile pictures
- ISBN barcode scanner integration
- Overdue book notifications
- Email reminders
- Multi-language support
