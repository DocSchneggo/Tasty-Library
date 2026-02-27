import sys
import sqlite3 as sql
import json as jsn
import yaml as yml
from pathlib import Path
from datetime import datetime as dt
from typing import Optional, List, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QTableWidget, QTableWidgetItem, QLineEdit,
    QLabel, QDialog, QFormLayout, QMessageBox, QFileDialog, QComboBox,
    QSpinBox, QDateEdit, QTextEdit, QHeaderView, QInputDialog,
    QProgressDialog, QStatusBar, QMenuBar, QMenu, QSplitter
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QFont, QColor

import lib
import codes


class LibraryManager:
    """Backend manager for library operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect_db()
    
    def connect_db(self):
        """Connect to the database"""
        try:
            self.conn = sql.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise Exception(f"Failed to connect to database: {str(e)}")
    
    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_all_users(self) -> List[Dict]:
        """Get all users from the database"""
        try:
            self.cursor.execute("SELECT id, name, state, created_at FROM users ORDER BY name")
            users = []
            for row in self.cursor.fetchall():
                users.append({
                    'id': row[0],
                    'name': row[1],
                    'state': row[2],
                    'created_at': row[3]
                })
            return users
        except Exception as e:
            raise Exception(f"Error fetching users: {str(e)}")
    
    def get_all_books(self) -> List[Dict]:
        """Get all books from the database"""
        try:
            self.cursor.execute("""
                SELECT id, title, author, isbn, borrowed_by, borrowed_at, description 
                FROM books ORDER BY title
            """)
            books = []
            for row in self.cursor.fetchall():
                books.append({
                    'id': row[0],
                    'title': row[1],
                    'author': row[2],
                    'isbn': row[3],
                    'borrowed_by': row[4],
                    'borrowed_at': row[5],
                    'description': row[6]
                })
            return books
        except Exception as e:
            raise Exception(f"Error fetching books: {str(e)}")
    
    def get_active_borrows(self) -> List[Dict]:
        """Get all active borrows"""
        try:
            self.cursor.execute("""
                SELECT b.id, b.book_id, bk.title, b.borrower_id, u.name, 
                       b.created_at, b.return_date, b.delayed
                FROM borrows b
                JOIN books bk ON b.book_id = bk.id
                JOIN users u ON b.borrower_id = u.id
                WHERE bk.borrowed_by IS NOT NULL
                ORDER BY b.created_at DESC
            """)
            borrows = []
            for row in self.cursor.fetchall():
                borrows.append({
                    'id': row[0],
                    'book_id': row[1],
                    'title': row[2],
                    'borrower_id': row[3],
                    'borrower_name': row[4],
                    'borrowed_at': row[5],
                    'return_date': row[6],
                    'delayed': row[7]
                })
            return borrows
        except Exception as e:
            raise Exception(f"Error fetching borrows: {str(e)}")
    
    def add_user(self, name: str, state: int = 0) -> bool:
        """Add a new user"""
        try:
            created_at = dt.now().isoformat()
            self.cursor.execute(
                "INSERT INTO users (name, state, created_at) VALUES (?, ?, ?)",
                (name, state, created_at)
            )
            self.conn.commit()
            return True
        except sql.IntegrityError:
            raise Exception(f"User '{name}' already exists")
        except Exception as e:
            raise Exception(f"Error adding user: {str(e)}")
    
    def remove_user(self, user_id: int) -> bool:
        """Remove a user"""
        try:
            self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            self.conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error removing user: {str(e)}")
    
    def add_book(self, title: str, author: str, isbn: str, description: str = "") -> bool:
        """Add a new book"""
        try:
            created_at = dt.now().isoformat()
            self.cursor.execute(
                """INSERT INTO books (title, author, isbn, description, created_at) 
                   VALUES (?, ?, ?, ?, ?)""",
                (title, author, isbn, description, created_at)
            )
            self.conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error adding book: {str(e)}")
    
    def remove_book(self, book_id: int) -> bool:
        """Remove a book"""
        try:
            self.cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
            self.conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error removing book: {str(e)}")
    
    def borrow_book(self, book_id: int, user_id: int, return_date: str = None) -> bool:
        """Borrow a book"""
        try:
            created_at = dt.now().isoformat()
            # Update book
            self.cursor.execute(
                "UPDATE books SET borrowed_by = ?, borrowed_at = ? WHERE id = ?",
                (user_id, created_at, book_id)
            )
            # Create borrow record
            self.cursor.execute(
                """INSERT INTO borrows (book_id, borrower_id, created_at, return_date, renewed, delayed) 
                   VALUES (?, ?, ?, ?, 0, 0)""",
                (book_id, user_id, created_at, return_date)
            )
            self.conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error borrowing book: {str(e)}")
    
    def return_book(self, book_id: int) -> bool:
        """Return a book"""
        try:
            # Update book
            self.cursor.execute(
                "UPDATE books SET borrowed_by = NULL, borrowed_at = NULL WHERE id = ?",
                (book_id,)
            )
            # Update borrow record
            self.cursor.execute(
                "UPDATE borrows SET return_date = ? WHERE book_id = ? AND return_date IS NULL",
                (dt.now().isoformat(), book_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            raise Exception(f"Error returning book: {str(e)}")


class AddUserDialog(QDialog):
    """Dialog for adding a new user"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New User")
        self.setModal(True)
        self.setGeometry(100, 100, 400, 200)
        
        layout = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter username")
        
        self.state_combo = QComboBox()
        self.state_combo.addItems(["Active", "Inactive", "Banned"])
        
        layout.addRow("Username:", self.name_input)
        layout.addRow("Status:", self.state_combo)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Add")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
    
    def get_data(self):
        return self.name_input.text(), self.state_combo.currentIndex()


class AddBookDialog(QDialog):
    """Dialog for adding a new book"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Book")
        self.setModal(True)
        self.setGeometry(100, 100, 450, 300)
        
        layout = QFormLayout()
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Book title")
        
        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Author name")
        
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("ISBN")
        
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Description (optional)")
        self.desc_input.setMaximumHeight(100)
        
        layout.addRow("Title:", self.title_input)
        layout.addRow("Author:", self.author_input)
        layout.addRow("ISBN:", self.isbn_input)
        layout.addRow("Description:", self.desc_input)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Add")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
    
    def get_data(self):
        return (
            self.title_input.text(),
            self.author_input.text(),
            self.isbn_input.text(),
            self.desc_input.toPlainText()
        )


class BorrowDialog(QDialog):
    """Dialog for borrowing a book"""
    
    def __init__(self, books: List[Dict], users: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Borrow Book")
        self.setModal(True)
        self.setGeometry(100, 100, 450, 250)
        
        layout = QFormLayout()
        
        self.book_combo = QComboBox()
        for book in books:
            if book['borrowed_by'] is None:
                self.book_combo.addItem(book['title'], book['id'])
        
        self.user_combo = QComboBox()
        for user in users:
            self.user_combo.addItem(user['name'], user['id'])
        
        self.return_date = QDateEdit()
        self.return_date.setDate(QDate.currentDate().addDays(30))
        self.return_date.setCalendarPopup(True)
        
        layout.addRow("Book:", self.book_combo)
        layout.addRow("User:", self.user_combo)
        layout.addRow("Return Date:", self.return_date)
        
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Borrow")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addRow(button_layout)
        self.setLayout(layout)
    
    def get_data(self):
        return (
            self.book_combo.currentData(),
            self.user_combo.currentData(),
            self.return_date.date().toString(Qt.DateFormat.ISODate)
        )


class TastyLibraryGUI(QMainWindow):
    """Main GUI application for Tasty Library"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tasty Library - Library Management System")
        self.setGeometry(100, 100, 1200, 700)
        
        self.manager = None
        self.db_path = None
        
        self.init_ui()
        self.show_connection_dialog()
    
    def init_ui(self):
        """Initialize the user interface"""
        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        connect_action = file_menu.addAction("Connect to Database")
        connect_action.triggered.connect(self.show_connection_dialog)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        self.status_label = QLabel("No database connected")
        self.status_label.setFont(QFont("Arial", 10))
        toolbar_layout.addWidget(self.status_label)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Users tab
        self.users_tab = self.create_users_tab()
        self.tabs.addTab(self.users_tab, "Users")
        
        # Books tab
        self.books_tab = self.create_books_tab()
        self.tabs.addTab(self.books_tab, "Books")
        
        # Borrows tab
        self.borrows_tab = self.create_borrows_tab()
        self.tabs.addTab(self.borrows_tab, "Borrowing")
        
        layout.addWidget(self.tabs)
        
        central_widget.setLayout(layout)
    
    def create_users_tab(self) -> QWidget:
        """Create the users management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add User")
        remove_btn = QPushButton("Remove Selected")
        refresh_btn = QPushButton("Refresh")
        
        add_btn.clicked.connect(self.add_user)
        remove_btn.clicked.connect(self.remove_user)
        refresh_btn.clicked.connect(self.load_users)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(4)
        self.users_table.setHorizontalHeaderLabels(["ID", "Username", "Status", "Created"])
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.users_table)
        widget.setLayout(layout)
        
        return widget
    
    def create_books_tab(self) -> QWidget:
        """Create the books management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        add_btn = QPushButton("Add Book")
        remove_btn = QPushButton("Remove Selected")
        refresh_btn = QPushButton("Refresh")
        
        add_btn.clicked.connect(self.add_book)
        remove_btn.clicked.connect(self.remove_book)
        refresh_btn.clicked.connect(self.load_books)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.books_table = QTableWidget()
        self.books_table.setColumnCount(6)
        self.books_table.setHorizontalHeaderLabels(["ID", "Title", "Author", "ISBN", "Borrowed By", "Description"])
        self.books_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.books_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.books_table)
        widget.setLayout(layout)
        
        return widget
    
    def create_borrows_tab(self) -> QWidget:
        """Create the borrowing management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        borrow_btn = QPushButton("Borrow Book")
        return_btn = QPushButton("Return Selected")
        refresh_btn = QPushButton("Refresh")
        
        borrow_btn.clicked.connect(self.borrow_book)
        return_btn.clicked.connect(self.return_book)
        refresh_btn.clicked.connect(self.load_borrows)
        
        toolbar.addWidget(borrow_btn)
        toolbar.addWidget(return_btn)
        toolbar.addWidget(refresh_btn)
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Table
        self.borrows_table = QTableWidget()
        self.borrows_table.setColumnCount(7)
        self.borrows_table.setHorizontalHeaderLabels(
            ["ID", "Book Title", "Borrower", "Borrowed Date", "Return Date", "Delayed", "Actions"]
        )
        self.borrows_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.borrows_table)
        widget.setLayout(layout)
        
        return widget
    
    def show_connection_dialog(self):
        """Show database connection dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Database File",
            "",
            "Database Files (*.db);;All Files (*.*)"
        )
        
        if file_path:
            try:
                self.manager = LibraryManager(file_path)
                self.db_path = file_path
                self.status_label.setText(f"Connected: {Path(file_path).name}")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Connection Error", str(e))
    
    def load_data(self):
        """Load all data from database"""
        try:
            self.load_users()
            self.load_books()
            self.load_borrows()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
    
    def load_users(self):
        """Load and display users"""
        if not self.manager:
            return
        
        try:
            users = self.manager.get_all_users()
            self.users_table.setRowCount(len(users))
            
            state_names = ["Active", "Inactive", "Banned"]
            
            for row, user in enumerate(users):
                self.users_table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
                self.users_table.setItem(row, 1, QTableWidgetItem(user['name']))
                self.users_table.setItem(row, 2, QTableWidgetItem(state_names[user['state']]))
                self.users_table.setItem(row, 3, QTableWidgetItem(user['created_at'][:10]))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load users: {str(e)}")
    
    def load_books(self):
        """Load and display books"""
        if not self.manager:
            return
        
        try:
            books = self.manager.get_all_books()
            self.books_table.setRowCount(len(books))
            
            for row, book in enumerate(books):
                self.books_table.setItem(row, 0, QTableWidgetItem(str(book['id'])))
                self.books_table.setItem(row, 1, QTableWidgetItem(book['title']))
                self.books_table.setItem(row, 2, QTableWidgetItem(book['author']))
                self.books_table.setItem(row, 3, QTableWidgetItem(book['isbn']))
                borrowed = book['borrowed_by'] if book['borrowed_by'] else "Available"
                self.books_table.setItem(row, 4, QTableWidgetItem(str(borrowed)))
                self.books_table.setItem(row, 5, QTableWidgetItem(book['description'] or ""))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load books: {str(e)}")
    
    def load_borrows(self):
        """Load and display active borrows"""
        if not self.manager:
            return
        
        try:
            borrows = self.manager.get_active_borrows()
            self.borrows_table.setRowCount(len(borrows))
            
            for row, borrow in enumerate(borrows):
                self.borrows_table.setItem(row, 0, QTableWidgetItem(str(borrow['id'])))
                self.borrows_table.setItem(row, 1, QTableWidgetItem(borrow['title']))
                self.borrows_table.setItem(row, 2, QTableWidgetItem(borrow['borrower_name']))
                self.borrows_table.setItem(row, 3, QTableWidgetItem(borrow['borrowed_at'][:10]))
                self.borrows_table.setItem(row, 4, QTableWidgetItem(borrow['return_date'] or "Not set"))
                delayed = "Yes" if borrow['delayed'] else "No"
                self.borrows_table.setItem(row, 5, QTableWidgetItem(delayed))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load borrows: {str(e)}")
    
    def add_user(self):
        """Add a new user"""
        if not self.manager:
            QMessageBox.warning(self, "Warning", "No database connected")
            return
        
        dialog = AddUserDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, state = dialog.get_data()
            if name:
                try:
                    self.manager.add_user(name, state)
                    self.load_users()
                    QMessageBox.information(self, "Success", f"User '{name}' added successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
            else:
                QMessageBox.warning(self, "Warning", "Please enter a username")
    
    def remove_user(self):
        """Remove selected user"""
        if not self.manager:
            QMessageBox.warning(self, "Warning", "No database connected")
            return
        
        current_row = self.users_table.currentRow()
        if current_row >= 0:
            user_id = int(self.users_table.item(current_row, 0).text())
            user_name = self.users_table.item(current_row, 1).text()
            
            reply = QMessageBox.question(
                self,
                "Confirm",
                f"Remove user '{user_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.manager.remove_user(user_id)
                    self.load_users()
                    QMessageBox.information(self, "Success", "User removed successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "Please select a user")
    
    def add_book(self):
        """Add a new book"""
        if not self.manager:
            QMessageBox.warning(self, "Warning", "No database connected")
            return
        
        dialog = AddBookDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            title, author, isbn, description = dialog.get_data()
            if title and author and isbn:
                try:
                    self.manager.add_book(title, author, isbn, description)
                    self.load_books()
                    QMessageBox.information(self, "Success", f"Book '{title}' added successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
            else:
                QMessageBox.warning(self, "Warning", "Please fill in all required fields")
    
    def remove_book(self):
        """Remove selected book"""
        if not self.manager:
            QMessageBox.warning(self, "Warning", "No database connected")
            return
        
        current_row = self.books_table.currentRow()
        if current_row >= 0:
            book_id = int(self.books_table.item(current_row, 0).text())
            book_title = self.books_table.item(current_row, 1).text()
            
            reply = QMessageBox.question(
                self,
                "Confirm",
                f"Remove book '{book_title}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                try:
                    self.manager.remove_book(book_id)
                    self.load_books()
                    self.load_borrows()
                    QMessageBox.information(self, "Success", "Book removed successfully")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "Please select a book")
    
    def borrow_book(self):
        """Borrow a book"""
        if not self.manager:
            QMessageBox.warning(self, "Warning", "No database connected")
            return
        
        users = self.manager.get_all_users()
        books = self.manager.get_all_books()
        
        if not users or not books:
            QMessageBox.warning(self, "Warning", "Please add users and books first")
            return
        
        dialog = BorrowDialog(books, users, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            book_id, user_id, return_date = dialog.get_data()
            
            try:
                self.manager.borrow_book(book_id, user_id, return_date)
                self.load_books()
                self.load_borrows()
                QMessageBox.information(self, "Success", "Book borrowed successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
    
    def return_book(self):
        """Return selected book"""
        if not self.manager:
            QMessageBox.warning(self, "Warning", "No database connected")
            return
        
        current_row = self.borrows_table.currentRow()
        if current_row >= 0:
            book_id = int(self.borrows_table.item(current_row, 1).text())  # Get book ID from title lookup
            book_title = self.borrows_table.item(current_row, 1).text()
            
            reply = QMessageBox.question(
                self,
                "Confirm",
                f"Return '{book_title}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Get book ID by title
                books = self.manager.get_all_books()
                book_id = None
                for book in books:
                    if book['title'] == book_title:
                        book_id = book['id']
                        break
                
                if book_id:
                    try:
                        self.manager.return_book(book_id)
                        self.load_books()
                        self.load_borrows()
                        QMessageBox.information(self, "Success", "Book returned successfully")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", str(e))
        else:
            QMessageBox.warning(self, "Warning", "Please select a borrowed book")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.manager:
            self.manager.close_db()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = TastyLibraryGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
