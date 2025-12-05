"""
Main window UI for the Email Summarizer application.
"""
import logging
from typing import List, Optional
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, 
    QLabel, QPushButton, QFrame, QSizePolicy, QSpacerItem, QToolBar,
    QStatusBar, QMessageBox, QProgressBar, QLineEdit, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QAction, QKeySequence, QShortcut

from models import EmailItem, AppSettings, EmailFilter
from theming import (
    get_email_card_stylesheet, get_toolbar_stylesheet, 
    get_scroll_area_stylesheet, get_loading_stylesheet
)
from workers import EmailRefreshController
from ui_settings import SettingsDialog
from email_actions import EmailActionWorker
from PySide6.QtCore import QThreadPool


logger = logging.getLogger(__name__)


class EmailCard(QFrame):
    """
    Widget representing a single email in the list.
    
    Shows sender, subject, date, summary, and action buttons.
    """
    
    # Signals for email actions
    mark_read_clicked = Signal(str)  # message_id
    mark_unread_clicked = Signal(str)
    delete_clicked = Signal(str)
    archive_clicked = Signal(str)
    
    def __init__(self, email: EmailItem, parent=None):
        """
        Initialize email card.
        
        Args:
            email: EmailItem to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.email = email
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the card UI."""
        self.setObjectName("email_card")
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet(get_email_card_stylesheet())
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        
        # Header row: sender and date
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sender
        self.sender_label = QLabel(self.email.sender_display)
        self.sender_label.setObjectName("sender_label")
        self.sender_label.setWordWrap(True)
        header_layout.addWidget(self.sender_label)
        
        # Spacer
        header_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        
        # Date with tooltip
        self.date_label = QLabel(self.email.date_display)
        self.date_label.setObjectName("date_label")
        self.date_label.setToolTip(self.email.date_tooltip)
        self.date_label.setAlignment(Qt.AlignRight)
        header_layout.addWidget(self.date_label)
        
        layout.addLayout(header_layout)
        
        # Subject
        self.subject_label = QLabel(self.email.subject)
        self.subject_label.setObjectName("subject_label")
        self.subject_label.setWordWrap(True)
        layout.addWidget(self.subject_label)
        
        # Summary
        summary_text = self.email.summary or "Generating summary..."
        self.summary_label = QLabel(summary_text)
        self.summary_label.setObjectName("summary_label")
        self.summary_label.setWordWrap(True)
        self.summary_label.setAlignment(Qt.AlignTop)
        # Set minimum height to avoid jumping when summary loads
        self.summary_label.setMinimumHeight(50)
        layout.addWidget(self.summary_label)
        
        # Action buttons row
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 8, 0, 0)
        actions_layout.setSpacing(8)
        
        # Mark as read button
        self.mark_read_btn = QPushButton("✓ Mark Read")
        self.mark_read_btn.setMaximumWidth(100)
        self.mark_read_btn.setStyleSheet(
            "QPushButton { background-color: rgba(60, 60, 70, 255); color: rgba(200, 200, 210, 255); "
            "border: 1px solid rgba(80, 80, 90, 255); border-radius: 4px; padding: 4px 8px; font-size: 11px; } "
            "QPushButton:hover { background-color: rgba(70, 70, 80, 255); }"
        )
        self.mark_read_btn.clicked.connect(lambda: self.mark_read_clicked.emit(self.email.message_id or ""))
        actions_layout.addWidget(self.mark_read_btn)
        
        # Delete button
        self.delete_btn = QPushButton("🗑️ Delete")
        self.delete_btn.setMaximumWidth(90)
        self.delete_btn.setStyleSheet(
            "QPushButton { background-color: rgba(120, 40, 40, 255); color: rgba(255, 255, 255, 255); "
            "border: 1px solid rgba(140, 50, 50, 255); border-radius: 4px; padding: 4px 8px; font-size: 11px; } "
            "QPushButton:hover { background-color: rgba(140, 50, 50, 255); }"
        )
        self.delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self.email.message_id or ""))
        actions_layout.addWidget(self.delete_btn)
        
        # Spacer
        actions_layout.addStretch()
        
        # Attachment indicator
        if self.email.has_attachments:
            attachment_label = QLabel("📎 Attachments")
            attachment_label.setStyleSheet("color: rgba(180, 180, 190, 255); font-size: 11px;")
            actions_layout.addWidget(attachment_label)
        
        layout.addLayout(actions_layout)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    def update_summary(self, summary: str):
        """Update the email summary text."""
        self.summary_label.setText(summary)
        self.email.summary = summary
    
    def mousePressEvent(self, event):
        """Handle mouse press for future email viewing feature."""
        if event.button() == Qt.LeftButton:
            # Future: Show email detail view
            logger.info(f"Email clicked: {self.email.subject}")
        super().mousePressEvent(event)


class EmailListWidget(QScrollArea):
    """
    Scrollable list of email cards.
    """
    
    # Signals for email actions
    email_action_requested = Signal(str, str)  # action, message_id
    
    def __init__(self, parent=None):
        """Initialize the email list widget."""
        super().__init__(parent)
        self._setup_ui()
        self._emails: List[EmailItem] = []
        self._filtered_emails: List[EmailItem] = []
        self._current_filter = EmailFilter()
    
    def _setup_ui(self):
        """Set up the scroll area UI."""
        self.setStyleSheet(get_scroll_area_stylesheet())
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(8, 8, 8, 8)
        self.container_layout.setSpacing(8)
        
        # Initially show empty state
        self._show_empty_state()
        
        self.setWidget(self.container)
    
    def _show_empty_state(self):
        """Show empty state message."""
        self._clear_layout()
        
        empty_label = QLabel("No emails to display")
        empty_label.setAlignment(Qt.AlignCenter)
        empty_label.setStyleSheet(
            "color: rgba(180, 180, 190, 255); font-size: 16px; padding: 40px;"
        )
        self.container_layout.addWidget(empty_label)
        
        hint_label = QLabel("Click 'Refresh' to fetch emails from your inbox")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet(
            "color: rgba(150, 150, 160, 255); font-size: 12px; padding-bottom: 20px;"
        )
        self.container_layout.addWidget(hint_label)
        
        # Add stretch to center the content
        self.container_layout.addStretch()
    
    def _show_loading_state(self, message: str = "Loading..."):
        """Show loading state with message."""
        self._clear_layout()
        
        # Loading message
        loading_label = QLabel(message)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet(
            "color: rgba(240, 240, 245, 255); font-size: 14px; padding: 20px;"
        )
        self.container_layout.addWidget(loading_label)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate
        progress.setStyleSheet(get_loading_stylesheet())
        progress.setMaximumWidth(300)
        progress.setAlignment(Qt.AlignCenter)
        self.container_layout.addWidget(progress, 0, Qt.AlignCenter)
        
        # Add stretch
        self.container_layout.addStretch()
    
    def _clear_layout(self):
        """Clear all widgets from the layout."""
        while self.container_layout.count():
            child = self.container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def set_emails(self, emails: List[EmailItem]):
        """
        Set the list of emails to display.
        
        Args:
            emails: List of EmailItem objects
        """
        self._emails = emails
        self._apply_filter()
    
    def apply_filter(self, email_filter: EmailFilter):
        """Apply filter to email list."""
        self._current_filter = email_filter
        self._apply_filter()
    
    def _apply_filter(self):
        """Apply current filter and update display."""
        if self._current_filter.is_active():
            self._filtered_emails = [
                email for email in self._emails 
                if email.matches_filter(self._current_filter)
            ]
        else:
            self._filtered_emails = self._emails
        
        self._display_emails()
    
    def _display_emails(self):
        """Display the filtered email list."""
        self._clear_layout()
        
        if not self._filtered_emails:
            if self._current_filter.is_active():
                # Show "no results" message
                empty_label = QLabel("No emails match the current filter")
                empty_label.setAlignment(Qt.AlignCenter)
                empty_label.setStyleSheet(
                    "color: rgba(180, 180, 190, 255); font-size: 16px; padding: 40px;"
                )
                self.container_layout.addWidget(empty_label)
                self.container_layout.addStretch()
            else:
                self._show_empty_state()
            return
        
        # Create email cards
        for email in self._filtered_emails:
            card = EmailCard(email)
            # Connect action signals
            card.mark_read_clicked.connect(lambda msg_id, a='mark_read': self.email_action_requested.emit(a, msg_id))
            card.delete_clicked.connect(lambda msg_id, a='delete': self.email_action_requested.emit(a, msg_id))
            self.container_layout.addWidget(card)
        
        # Add stretch at the end
        self.container_layout.addStretch()
        
        # Scroll to top
        self.verticalScrollBar().setValue(0)
    
    def show_loading(self, message: str = "Loading emails..."):
        """Show loading state."""
        self._show_loading_state(message)
    
    def update_email_summary(self, email_index: int, summary: str):
        """
        Update summary for a specific email.
        
        Args:
            email_index: Index of email in the list
            summary: New summary text
        """
        if 0 <= email_index < len(self._emails):
            # Find the corresponding card widget
            for i in range(self.container_layout.count()):
                item = self.container_layout.itemAt(i)
                if item and isinstance(item.widget(), EmailCard):
                    card = item.widget()
                    if card.email == self._emails[email_index]:
                        card.update_summary(summary)
                        break


class MainWindow(QMainWindow):
    """
    Main application window.
    """
    
    def __init__(self, app_settings: Optional[AppSettings] = None):
        """
        Initialize main window.
        
        Args:
            app_settings: Application settings
        """
        super().__init__()
        self.app_settings = app_settings
        
        # Email refresh controller
        self.refresh_controller = EmailRefreshController(self)
        
        # Thread pool for email actions
        self.thread_pool = QThreadPool()
        
        # Setup UI and connections
        self._setup_ui()
        self._setup_connections()
        self._setup_keyboard_shortcuts()
        
        # Auto-refresh timer
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._on_auto_refresh)
        
        # Initial setup
        if self.app_settings and self.app_settings.auto_refresh_on_startup:
            # Delay auto-refresh to let UI fully initialize
            QTimer.singleShot(1000, self._refresh_emails)
    
    def _setup_ui(self):
        """Set up the main window UI."""
        self.setWindowTitle("📧 Email Summarizer — Last 10")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        self._setup_toolbar()
        
        # Email list
        self.email_list = EmailListWidget()
        layout.addWidget(self.email_list)
        
        # Status bar
        self._setup_status_bar()
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        self.toolbar = QToolBar()
        self.toolbar.setStyleSheet(get_toolbar_stylesheet())
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        
        # Account selector
        if self.app_settings and len(self.app_settings.imap_accounts) > 1:
            self.account_combo = QComboBox()
            self.account_combo.setToolTip("Select email account")
            for account in self.app_settings.imap_accounts:
                self.account_combo.addItem(account.get_display_name())
            self.account_combo.setCurrentIndex(self.app_settings.active_account_index)
            self.account_combo.currentIndexChanged.connect(self._on_account_changed)
            self.toolbar.addWidget(self.account_combo)
            self.toolbar.addSeparator()
        else:
            self.account_combo = None
        
        # Refresh action
        self.refresh_action = QAction("🔄 Refresh", self)
        self.refresh_action.setShortcut(QKeySequence("Ctrl+R"))
        self.refresh_action.setToolTip("Refresh emails from server (Ctrl+R)")
        self.refresh_action.triggered.connect(self._refresh_emails)
        self.toolbar.addAction(self.refresh_action)
        
        self.toolbar.addSeparator()
        
        # Search bar
        search_label = QLabel("🔍 ")
        self.toolbar.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search emails...")
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.toolbar.addWidget(self.search_input)
        
        # Clear search button
        self.clear_search_action = QAction("✕", self)
        self.clear_search_action.setToolTip("Clear search")
        self.clear_search_action.triggered.connect(self._clear_search)
        self.toolbar.addAction(self.clear_search_action)
        
        self.toolbar.addSeparator()
        
        # Settings action
        self.settings_action = QAction("⚙️ Settings", self)
        self.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.settings_action.setToolTip("Open settings (Ctrl+,)")
        self.settings_action.triggered.connect(self._show_settings)
        self.toolbar.addAction(self.settings_action)
        
        # About action
        self.about_action = QAction("ℹ️ About", self)
        self.about_action.setToolTip("About Email Summarizer")
        self.about_action.triggered.connect(self._show_about)
        self.toolbar.addAction(self.about_action)
        
        # Help/Shortcuts action
        self.shortcuts_action = QAction("⌨️ Shortcuts", self)
        self.shortcuts_action.setShortcut(QKeySequence("F1"))
        self.shortcuts_action.setToolTip("Show keyboard shortcuts (F1)")
        self.shortcuts_action.triggered.connect(self._show_keyboard_shortcuts)
        self.toolbar.addAction(self.shortcuts_action)
        
        self.addToolBar(self.toolbar)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status message
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Connection status (right side)
        self.connection_label = QLabel("")
        self.status_bar.addPermanentWidget(self.connection_label)
        
        # Update initial status
        self._update_connection_status()
    
    def _setup_connections(self):
        """Set up signal connections."""
        # Refresh controller signals
        self.refresh_controller.refresh_started.connect(self._on_refresh_started)
        self.refresh_controller.progress_updated.connect(self._on_progress_updated)
        self.refresh_controller.emails_updated.connect(self._on_emails_updated)
        self.refresh_controller.refresh_completed.connect(self._on_refresh_completed)
        
        # Email action signals
        self.email_list.email_action_requested.connect(self._handle_email_action)
    
    def _setup_keyboard_shortcuts(self):
        """Set up keyboard shortcuts for the application."""
        # Focus search (Ctrl+F)
        self.shortcut_focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_focus_search.activated.connect(self._focus_search)
        
        # Clear search (Escape when search has focus)
        self.shortcut_clear_search = QShortcut(QKeySequence("Escape"), self.search_input)
        self.shortcut_clear_search.activated.connect(self._clear_search)
        
        # Quit application (Ctrl+Q)
        self.shortcut_quit = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.shortcut_quit.activated.connect(self.close)
        
        # Help/Keyboard shortcuts dialog (F1 or Ctrl+?)
        self.shortcut_help = QShortcut(QKeySequence("F1"), self)
        self.shortcut_help.activated.connect(self._show_keyboard_shortcuts)
        
        # Navigation shortcuts
        # Scroll down (J - like Vim/Gmail)
        self.shortcut_scroll_down = QShortcut(QKeySequence("J"), self)
        self.shortcut_scroll_down.activated.connect(self._scroll_down)
        
        # Scroll up (K - like Vim/Gmail)
        self.shortcut_scroll_up = QShortcut(QKeySequence("K"), self)
        self.shortcut_scroll_up.activated.connect(self._scroll_up)
        
        # Next account (Ctrl+Tab)
        if self.account_combo:
            self.shortcut_next_account = QShortcut(QKeySequence("Ctrl+Tab"), self)
            self.shortcut_next_account.activated.connect(self._switch_to_next_account)
            
            # Previous account (Ctrl+Shift+Tab)
            self.shortcut_prev_account = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
            self.shortcut_prev_account.activated.connect(self._switch_to_prev_account)
        
        logger.info("Keyboard shortcuts initialized")
    
    def _focus_search(self):
        """Focus the search input field."""
        self.search_input.setFocus()
        self.search_input.selectAll()
        self.status_label.setText("Search mode - Type to filter emails")
    
    def _scroll_down(self):
        """Scroll the email list down."""
        scrollbar = self.email_list.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() + 100)  # Scroll by 100 pixels
    
    def _scroll_up(self):
        """Scroll the email list up."""
        scrollbar = self.email_list.verticalScrollBar()
        scrollbar.setValue(scrollbar.value() - 100)  # Scroll by 100 pixels
    
    def _switch_to_next_account(self):
        """Switch to the next email account."""
        if self.account_combo and self.account_combo.count() > 1:
            current = self.account_combo.currentIndex()
            next_index = (current + 1) % self.account_combo.count()
            self.account_combo.setCurrentIndex(next_index)
    
    def _switch_to_prev_account(self):
        """Switch to the previous email account."""
        if self.account_combo and self.account_combo.count() > 1:
            current = self.account_combo.currentIndex()
            prev_index = (current - 1) % self.account_combo.count()
            self.account_combo.setCurrentIndex(prev_index)
    
    def _show_keyboard_shortcuts(self):
        """Show dialog with all keyboard shortcuts."""
        shortcuts_text = (
            "<h3>⌨️ Keyboard Shortcuts</h3>"
            "<table style='width: 100%;'>"
            "<tr><th align='left'>Action</th><th align='left'>Shortcut</th></tr>"
            "<tr><td><b>General</b></td><td></td></tr>"
            "<tr><td>Refresh emails</td><td><code>Ctrl+R</code></td></tr>"
            "<tr><td>Open settings</td><td><code>Ctrl+,</code></td></tr>"
            "<tr><td>Quit application</td><td><code>Ctrl+Q</code></td></tr>"
            "<tr><td>Show shortcuts</td><td><code>F1</code></td></tr>"
            "<tr><td>&nbsp;</td><td></td></tr>"
            "<tr><td><b>Search</b></td><td></td></tr>"
            "<tr><td>Focus search</td><td><code>Ctrl+F</code></td></tr>"
            "<tr><td>Clear search</td><td><code>Escape</code> (in search)</td></tr>"
            "<tr><td>&nbsp;</td><td></td></tr>"
            "<tr><td><b>Navigation</b></td><td></td></tr>"
            "<tr><td>Scroll down</td><td><code>J</code></td></tr>"
            "<tr><td>Scroll up</td><td><code>K</code></td></tr>"
        )
        
        if self.account_combo and self.account_combo.count() > 1:
            shortcuts_text += (
                "<tr><td>&nbsp;</td><td></td></tr>"
                "<tr><td><b>Accounts</b></td><td></td></tr>"
                "<tr><td>Next account</td><td><code>Ctrl+Tab</code></td></tr>"
                "<tr><td>Previous account</td><td><code>Ctrl+Shift+Tab</code></td></tr>"
            )
        
        shortcuts_text += "</table>"
        
        QMessageBox.information(self, "Keyboard Shortcuts", shortcuts_text)
    
    def _refresh_emails(self):
        """Start email refresh operation."""
        if not self.app_settings or not self.app_settings.imap.is_complete():
            self._show_settings_required_dialog()
            return
        
        if self.refresh_controller.is_refreshing():
            logger.info("Refresh already in progress")
            return
        
        # Start refresh
        self.refresh_controller.start_refresh(
            self.app_settings.imap,
            self.app_settings.max_emails_to_fetch
        )
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.app_settings, self)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.exec()
    
    def _show_about(self):
        """Show about dialog."""
        about_text = (
            "<h3>📧 Email Summarizer</h3>"
            "<p>A local, privacy-focused email summarizer that connects to your IMAP inbox "
            "and generates summaries using TextRank algorithm.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>• Secure IMAP connection with SSL/TLS</li>"
            "<li>• Local text summarization (no cloud APIs)</li>"
            "<li>• Dark themed interface</li>"
            "<li>• Credential storage in system keyring</li>"
            "<li>• Email search and filtering</li>"
            "<li>• Multiple account support</li>"
            "<li>• Desktop notifications (Windows)</li>"
            "<li>• Keyboard shortcuts (press F1)</li>"
            "<li>• Email actions (mark read, delete)</li>"
            "</ul>"
            "<p><b>Privacy:</b> All processing happens locally. No data is sent to external services.</p>"
            "<p><b>Tip:</b> Press <code>F1</code> to see all keyboard shortcuts.</p>"
            "<p><b>License:</b> MIT License</p>"
        )
        
        QMessageBox.about(self, "About Email Summarizer", about_text)
    
    def _on_search_changed(self, text: str):
        """Handle search text change."""
        email_filter = EmailFilter(search_query=text)
        self.email_list.apply_filter(email_filter)
        
        if text:
            self.status_label.setText(f"Searching: '{text}'")
        else:
            email_count = len(self.email_list._filtered_emails)
            self.status_label.setText(f"Showing {email_count} email{'s' if email_count != 1 else ''}")
    
    def _clear_search(self):
        """Clear search input."""
        self.search_input.clear()
    
    def _on_account_changed(self, index: int):
        """Handle account selection change."""
        if self.app_settings and 0 <= index < len(self.app_settings.imap_accounts):
            self.app_settings.set_active_account(index)
            self.status_label.setText(f"Switched to {self.app_settings.active_account.get_display_name()}")
            
            # Auto-refresh with new account
            QTimer.singleShot(500, self._refresh_emails)
    
    def _show_settings_required_dialog(self):
        """Show dialog indicating settings are required."""
        reply = QMessageBox.question(
            self,
            "Settings Required",
            "Email settings are not configured. Would you like to open settings now?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._show_settings()
    
    def _on_refresh_started(self):
        """Handle refresh start."""
        self.refresh_action.setEnabled(False)
        self.refresh_action.setText("🔄 Refreshing...")
        self.email_list.show_loading("Connecting to email server...")
        self.status_label.setText("Refreshing emails...")
    
    def _on_progress_updated(self, message: str):
        """Handle progress updates."""
        self.status_label.setText(message)
        self.email_list.show_loading(message)
    
    def _on_emails_updated(self, emails: List[EmailItem]):
        """Handle email list update."""
        self.email_list.set_emails(emails)
        email_count = len(emails)
        self.status_label.setText(f"Loaded {email_count} email{'s' if email_count != 1 else ''}")
    
    def _on_refresh_completed(self, success: bool, message: str):
        """Handle refresh completion."""
        self.refresh_action.setEnabled(True)
        self.refresh_action.setText("🔄 Refresh")
        
        if success:
            self.status_label.setText(message)
            self._update_connection_status(True)
        else:
            self.status_label.setText("Refresh failed")
            self._update_connection_status(False)
            
            # Show error dialog for connection issues
            if "Authentication" in message or "Connection" in message:
                QMessageBox.critical(
                    self,
                    "Email Refresh Failed",
                    f"Failed to refresh emails:\n\n{message}\n\n"
                    "Please check your settings and internet connection."
                )
    
    def _on_settings_saved(self, settings: AppSettings):
        """Handle settings save."""
        self.app_settings = settings
        self._update_connection_status()
        self.status_label.setText("Settings saved")
        
        # Optional: Auto-refresh after settings change
        QTimer.singleShot(1000, self._refresh_emails)
    
    def _on_auto_refresh(self):
        """Handle auto-refresh timer."""
        if not self.refresh_controller.is_refreshing():
            self._refresh_emails()
    
    def _handle_email_action(self, action: str, message_id: str):
        """Handle email action requests."""
        if not self.app_settings or not self.app_settings.imap:
            QMessageBox.warning(self, "Not Connected", "Please configure and connect to an email account first.")
            return
        
        if not message_id:
            logger.warning(f"Email action '{action}' called with no message ID")
            return
        
        # Confirm delete action
        if action == 'delete':
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                "Are you sure you want to delete this email?\n\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Create and run worker
        worker = EmailActionWorker(self.app_settings.imap, action, message_id)
        worker.signals.finished.connect(self._on_email_action_completed)
        worker.signals.error.connect(self._on_email_action_error)
        
        self.thread_pool.start(worker)
        self.status_label.setText(f"Processing: {action}...")
        logger.info(f"Executing email action: {action} on message {message_id}")
    
    def _on_email_action_completed(self, success: bool, message: str):
        """Handle email action completion."""
        if success:
            self.status_label.setText(message)
            # Refresh to show updated state
            QTimer.singleShot(500, self._refresh_emails)
        else:
            self.status_label.setText(f"Action failed: {message}")
            QMessageBox.warning(self, "Action Failed", f"Failed to perform email action:\n\n{message}")
    
    def _on_email_action_error(self, error: str):
        """Handle email action error."""
        self.status_label.setText(f"Error: {error}")
        QMessageBox.critical(self, "Error", f"An error occurred:\n\n{error}")
    
    def _update_connection_status(self, connected: Optional[bool] = None):
        """Update connection status indicator."""
        if connected is None:
            if self.app_settings and self.app_settings.imap.is_complete():
                status_text = "⚫ Configured"
                status_color = "#FFA500"  # Orange - configured but not connected
            else:
                status_text = "⚫ Not configured"
                status_color = "#F44336"  # Red
        elif connected:
            status_text = "🟢 Connected"
            status_color = "#4CAF50"  # Green
        else:
            status_text = "🔴 Connection failed"
            status_color = "#F44336"  # Red
        
        self.connection_label.setText(status_text)
        self.connection_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
    
    def closeEvent(self, event):
        """Handle application close."""
        # Cancel any ongoing refresh
        if self.refresh_controller.is_refreshing():
            self.refresh_controller.cancel_refresh()
        
        # Stop auto-refresh timer
        if self._auto_refresh_timer.isActive():
            self._auto_refresh_timer.stop()
        
        event.accept()
    
    def set_auto_refresh_interval(self, minutes: int):
        """
        Set auto-refresh interval.
        
        Args:
            minutes: Refresh interval in minutes (0 to disable)
        """
        if minutes > 0:
            self._auto_refresh_timer.start(minutes * 60 * 1000)  # Convert to milliseconds
            logger.info(f"Auto-refresh enabled: every {minutes} minutes")
        else:
            self._auto_refresh_timer.stop()
            logger.info("Auto-refresh disabled")
    
    def get_current_emails(self) -> List[EmailItem]:
        """Get currently displayed emails."""
        return self.email_list._emails.copy()
    
    def update_settings(self, settings: AppSettings):
        """Update application settings."""
        self.app_settings = settings
        self._update_connection_status()