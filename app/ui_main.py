"""
Main window UI for the Email Summarizer application.
"""
import logging
from typing import List, Optional
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, 
    QLabel, QPushButton, QFrame, QSizePolicy, QSpacerItem, QToolBar,
    QStatusBar, QMessageBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QAction

from models import EmailItem, AppSettings
from theming import (
    get_email_card_stylesheet, get_toolbar_stylesheet, 
    get_scroll_area_stylesheet, get_loading_stylesheet
)
from workers import EmailRefreshController
from ui_settings import SettingsDialog


logger = logging.getLogger(__name__)


class EmailCard(QFrame):
    """
    Widget representing a single email in the list.
    
    Shows sender, subject, date, and summary in a card layout.
    """
    
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
        
        # Attachment indicator
        if self.email.has_attachments:
            attachment_label = QLabel("📎 Has attachments")
            attachment_label.setStyleSheet("color: rgba(180, 180, 190, 255); font-size: 11px;")
            layout.addWidget(attachment_label)
        
        # Set size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        # Set cursor to indicate clickable (future feature)
        self.setCursor(Qt.PointingHandCursor)
    
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
    
    def __init__(self, parent=None):
        """Initialize the email list widget."""
        super().__init__(parent)
        self._setup_ui()
        self._emails: List[EmailItem] = []
    
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
        self._clear_layout()
        
        if not emails:
            self._show_empty_state()
            return
        
        # Create email cards
        for email in emails:
            card = EmailCard(email)
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
        
        # Setup UI and connections
        self._setup_ui()
        self._setup_connections()
        
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
        
        # Refresh action
        self.refresh_action = QAction("🔄 Refresh", self)
        self.refresh_action.setToolTip("Refresh emails from server")
        self.refresh_action.triggered.connect(self._refresh_emails)
        self.toolbar.addAction(self.refresh_action)
        
        self.toolbar.addSeparator()
        
        # Settings action
        self.settings_action = QAction("⚙️ Settings", self)
        self.settings_action.setToolTip("Open settings")
        self.settings_action.triggered.connect(self._show_settings)
        self.toolbar.addAction(self.settings_action)
        
        # About action
        self.about_action = QAction("ℹ️ About", self)
        self.about_action.setToolTip("About Email Summarizer")
        self.about_action.triggered.connect(self._show_about)
        self.toolbar.addAction(self.about_action)
        
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
            "</ul>"
            "<p><b>Privacy:</b> All processing happens locally. No data is sent to external services.</p>"
            "<p><b>License:</b> MIT License</p>"
        )
        
        QMessageBox.about(self, "About Email Summarizer", about_text)
    
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