#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
QDMBoxSearch - Quick and Dirty MBox Search Tool
---------------------------------
A professional desktop tool for searching through large mbox files.
Author: J.F. Durocher
Copyright (c) 2025 J.F. Durocher (jf@durocher.in)
"""

import os
import sys
import mailbox
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QProgressBar,
    QComboBox, QTextEdit, QSplitter, QMenuBar, QMenu, QStatusBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QAction, QKeySequence
import re

@dataclass
class EmailMessage:
    """Data class to store email message information."""
    message_id: str
    subject: str
    from_addr: str
    date: datetime
    body: str

class MBoxLoader(QThread):
    """Thread for loading mbox file to prevent UI freezing."""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, mbox_path: str):
        super().__init__()
        self.mbox_path = mbox_path

    def run(self):
        try:
            self.status.emit("Scanning file for messages...")
            # First pass: count messages and estimate progress
            message_count = 0
            file_size = os.path.getsize(self.mbox_path)
            bytes_processed = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            with open(self.mbox_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    bytes_processed += len(chunk)
                    # Look for message boundaries in the chunk
                    message_count += chunk.count(b'\nFrom ')
                    # Update progress based on file size
                    progress = int((bytes_processed / file_size) * 50)  # First 50% for scanning
                    self.progress.emit(progress)
            
            self.status.emit(f"Found {message_count} messages. Loading content...")
            
            # Second pass: load messages
            mbox = mailbox.mbox(self.mbox_path)
            messages = []
            current_message = 0
            
            for message in mbox:
                # Parse the date header safely
                date_header = message.get('Date', '')
                date_obj = None
                if date_header:
                    try:
                        date_obj = parsedate_to_datetime(date_header)
                    except Exception:
                        date_obj = None

                # Get message body
                body = ""
                html_body = ""
                if message.is_multipart():
                    for part in message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            try:
                                body += part.get_payload(decode=True).decode()
                            except:
                                continue
                        elif content_type == "text/html":
                            try:
                                html_body += part.get_payload(decode=True).decode()
                            except:
                                continue
                else:
                    try:
                        if message.get_content_type() == "text/html":
                            html_body = message.get_payload(decode=True).decode()
                        else:
                            body = message.get_payload(decode=True).decode()
                    except:
                        body = message.get_payload()

                email = EmailMessage(
                    message_id=message.get('Message-ID', ''),
                    subject=message.get('Subject', ''),
                    from_addr=message.get('From', ''),
                    date=date_obj,
                    body=html_body if html_body else body
                )
                messages.append(email)
                current_message += 1
                # Second 50% for loading messages
                progress = 50 + int((current_message / message_count) * 50)
                self.progress.emit(progress)
                self.status.emit(f"Loading message {current_message} of {message_count} ({current_message/message_count*100:.1f}%)")

            self.finished.emit(messages)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Main window of the application."""
    
    def __init__(self):
        super().__init__()
        # Set window icon based on platform
        if sys.platform == 'darwin':
            self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon.icns')))
        elif sys.platform == 'win32':
            self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon.ico')))
        else:
            self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon.png')))
        self.messages: List[EmailMessage] = []
        self.init_ui()
        self.create_menu_bar()

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # On macOS, create the application menu
        if sys.platform == 'darwin':
            app_menu = menubar.addMenu("QDMBoxSearch")
            
            # About action
            about_action = QAction("About QDMBoxSearch", self)
            about_action.setStatusTip("About QDMBoxSearch Tool")
            about_action.triggered.connect(self.show_about)
            app_menu.addAction(about_action)
            
            # Add separator
            app_menu.addSeparator()
            
            # Preferences action (disabled for now)
            prefs_action = QAction("Preferences...", self)
            prefs_action.setEnabled(False)
            app_menu.addAction(prefs_action)
            
            # Add separator
            app_menu.addSeparator()
            
            # Services menu
            services_menu = app_menu.addMenu("Services")
            
            # Add separator
            app_menu.addSeparator()
            
            # Hide action
            hide_action = QAction("Hide QDMBoxSearch", self)
            hide_action.setShortcut(QKeySequence("Ctrl+H"))
            hide_action.triggered.connect(self.hide)
            app_menu.addAction(hide_action)
            
            # Hide Others action
            hide_others_action = QAction("Hide Others", self)
            hide_others_action.setShortcut(QKeySequence("Ctrl+Alt+H"))
            app_menu.addAction(hide_others_action)
            
            # Show All action
            show_all_action = QAction("Show All", self)
            app_menu.addAction(show_all_action)
            
            # Add separator
            app_menu.addSeparator()
            
            # Quit action
            quit_action = QAction("Quit QDMBoxSearch", self)
            quit_action.setShortcut(QKeySequence.StandardKey.Quit)
            quit_action.triggered.connect(self.close)
            app_menu.addAction(quit_action)
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Open action
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an MBox file")
        open_action.triggered.connect(self.select_file)
        file_menu.addAction(open_action)
        
        # Add separator
        file_menu.addSeparator()
        
        # Exit action (only for non-macOS platforms)
        if sys.platform != 'darwin':
            exit_action = QAction("E&xit", self)
            exit_action.setShortcut(QKeySequence.StandardKey.Quit)
            exit_action.setStatusTip("Exit the application")
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
        
        # Help menu (only for non-macOS platforms)
        if sys.platform != 'darwin':
            help_menu = menubar.addMenu("&Help")
            
            # About action
            about_action = QAction("&About", self)
            about_action.setStatusTip("About QDMBoxSearch Tool")
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)

    def show_about(self):
        """Show the about dialog."""
        QMessageBox.about(self, "About QDMBoxSearch",
            "QDMBoxSearch - Quick and Dirty MBox Search Tool\n\n"
            "A professional tool for searching through large mbox files.\n\n"
            "Copyright (c) 2025 J.F. Durocher (jf@durocher.in)")

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("QDMBoxSearch")
        self.setMinimumSize(1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # File selection area
        file_layout = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("font-weight: bold;")
        file_layout.addWidget(self.file_label)
        layout.addLayout(file_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Search area
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter search query...")
        self.search_input.returnPressed.connect(self.search)
        
        self.search_type = QComboBox()
        self.search_type.addItems(["Subject", "Body", "Both"])
        
        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_type)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        # Results area
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Date", "From", "Subject"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.itemSelectionChanged.connect(self.show_selected_message)
        splitter.addWidget(self.results_table)

        # Message preview
        self.message_preview = QTextEdit()
        self.message_preview.setReadOnly(True)
        splitter.addWidget(self.message_preview)

        layout.addWidget(splitter)

        # Status bar
        self.statusBar().showMessage("Ready")

    def select_file(self):
        """Handle file selection."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select MBox File",
            "",
            "MBox Files (*.mbox);;All Files (*.*)"
        )
        
        if file_name:
            self.file_label.setText(os.path.basename(file_name))
            self.load_mbox(file_name)

    def load_mbox(self, file_path: str):
        """Load the mbox file in a separate thread."""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Initializing...")
        
        self.loader = MBoxLoader(file_path)
        self.loader.progress.connect(self.update_progress)
        self.loader.status.connect(self.update_status)
        self.loader.finished.connect(self.loading_finished)
        self.loader.error.connect(self.loading_error)
        self.loader.start()

    def update_progress(self, value: int):
        """Update the progress bar."""
        self.progress_bar.setValue(value)

    def update_status(self, message: str):
        """Update the status bar with the current operation."""
        self.statusBar().showMessage(message)

    def loading_finished(self, messages: List[EmailMessage]):
        """Handle completion of mbox loading."""
        self.messages = messages
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(f"Loaded {len(messages)} messages")
        self.search()  # Perform initial search to show all messages

    def loading_error(self, error_msg: str):
        """Handle loading errors."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Error loading mbox file: {error_msg}")

    def search(self):
        """Perform the search operation."""
        query = self.search_input.text().lower()
        search_type = self.search_type.currentText()
        
        results = []
        for message in self.messages:
            match = False
            subject = str(message.subject) if not isinstance(message.subject, str) else message.subject
            body = str(message.body) if not isinstance(message.body, str) else message.body
            
            if search_type in ["Subject", "Both"] and query in subject.lower():
                match = True
            if search_type in ["Body", "Both"] and query in body.lower():
                match = True
                
            if match:
                results.append(message)

        self.display_results(results)

    def display_results(self, results: List[EmailMessage]):
        """Display search results in the table."""
        self.results_table.setRowCount(0)
        
        for message in results:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            date_str = message.date.strftime("%Y-%m-%d %H:%M") if message.date else "Unknown"
            self.results_table.setItem(row, 0, QTableWidgetItem(date_str))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(message.from_addr)))
            self.results_table.setItem(row, 2, QTableWidgetItem(str(message.subject)))
            
            # Store the message object in the first column for reference
            self.results_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, message)

        self.statusBar().showMessage(f"Found {len(results)} results")

    def show_selected_message(self):
        """Display the selected message in the preview area."""
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            return
            
        row = selected_items[0].row()
        message = self.results_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        
        # Check if the body contains HTML
        is_html = bool(re.search(r'<[^>]+>', message.body))
        
        if is_html:
            # For HTML content, wrap it in a proper HTML document
            preview_text = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h3 {{ color: #2c3e50; }}
                    .header {{ color: #7f8c8d; margin-bottom: 20px; }}
                    .content {{ margin-top: 20px; }}
                </style>
            </head>
            <body>
                <h3>{message.subject}</h3>
                <div class="header">
                    <p><b>From:</b> {message.from_addr}</p>
                    <p><b>Date:</b> {message.date.strftime('%Y-%m-%d %H:%M') if message.date else 'Unknown'}</p>
                </div>
                <hr>
                <div class="content">
                    {message.body}
                </div>
            </body>
            </html>
            """
        else:
            # For plain text, use pre-formatted text
            preview_text = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h3 {{ color: #2c3e50; }}
                    .header {{ color: #7f8c8d; margin-bottom: 20px; }}
                    pre {{ white-space: pre-wrap; word-wrap: break-word; }}
                </style>
            </head>
            <body>
                <h3>{message.subject}</h3>
                <div class="header">
                    <p><b>From:</b> {message.from_addr}</p>
                    <p><b>Date:</b> {message.date.strftime('%Y-%m-%d %H:%M') if message.date else 'Unknown'}</p>
                </div>
                <hr>
                <pre>{message.body}</pre>
            </body>
            </html>
            """
        
        self.message_preview.setHtml(preview_text)

def main():
    """Main function to run the application."""
    app = QApplication(sys.argv)
    
    # Set application name and organization
    app.setApplicationName("QDMBoxSearch")
    app.setOrganizationName("J.F. Durocher")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 