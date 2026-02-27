# Tasty Library GUI - Quick Start Guide

## 🚀 Getting Started in 2 Minutes

### Step 1: Install PyQt6
```bash
pip install PyQt6
```

### Step 2: Launch the GUI
Choose ONE of these options:

**Windows (Batch):**
```bash
launch_gui.bat
```

**Windows (PowerShell):**
```powershell
.\launch_gui.ps1
```

**Any OS (Python):**
```bash
python gui_launcher.py
```

### Step 3: Connect Your Database
1. Click **File → Connect to Database**
2. Select your library database file (`.db`)
3. Done! The GUI is ready to use

---

## 📚 Basic Workflow

### Adding a New User
1. Go to **Users** tab
2. Click **Add User**
3. Enter username and select status
4. Click **Add**

### Adding a New Book
1. Go to **Books** tab
2. Click **Add Book**
3. Enter Title, Author, ISBN
4. Click **Add**

### Borrowing a Book
1. Go to **Borrowing** tab
2. Click **Borrow Book**
3. Select the book and user
4. Set return date (default: 30 days)
5. Click **Borrow**

### Returning a Book
1. Go to **Borrowing** tab
2. Select the borrowed book
3. Click **Return Selected**
4. Confirm

---

## 💡 Tips

- **Refresh Data**: Click the **Refresh** button in any tab to reload data from the database
- **Search**: Scroll through tables to find items (search feature coming soon)
- **Multiple Users**: Add all your library users first before borrowing
- **Database Backup**: Regularly backup your `.db` file!

---

## 🆘 Need Help?

- Check [GUI.md](GUI.md) for detailed documentation
- Ensure PyQt6 is installed: `pip install PyQt6`
- Database file must be in valid SQLite format

---

## 🔧 For Developers

The GUI architecture is modular:
- `LibraryManager` - Handles all database operations
- `TastyLibraryGUI` - Main window and UI
- Dialog classes - Specialized forms for input

Modify `gui.py` to customize appearance or functionality!
