"""
Settings dialog for IMAP configuration and application preferences.
"""
import os
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QLabel, QLineEdit, QSpinBox, QCheckBox, QPushButton, QTextEdit,
    QProgressBar, QMessageBox, QTabWidget, QWidget, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from dotenv import load_dotenv, set_key

from models import ImapConfig, AppSettings
from theming import get_dialog_stylesheet
from workers import ConnectionTestController


logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Settings dialog for IMAP configuration and application preferences.
    
    Supports both keyring and .env file storage for credentials.
    """
    
    # Signal emitted when settings are saved
    settings_saved = Signal(object)  # AppSettings
    
    def __init__(self, current_settings: Optional[AppSettings] = None, parent=None):
        """
        Initialize settings dialog.
        
        Args:
            current_settings: Current application settings
            parent: Parent widget
        """
        super().__init__(parent)
        self.current_settings = current_settings or self._create_default_settings()
        
        # Connection test controller
        self.test_controller = ConnectionTestController(self)
        self.test_controller.test_started.connect(self._on_test_started)
        self.test_controller.test_completed.connect(self._on_test_completed)
        
        self._setup_ui()
        self._load_current_settings()
        self._setup_connections()
    
    def _create_default_settings(self) -> AppSettings:
        """Create default settings."""
        return AppSettings(
            imap=ImapConfig(host="", port=993, username="", password=""),
            auto_refresh_on_startup=True,
            use_keyring=True
        )
    
    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Email Summarizer - Settings")
        self.setModal(True)
        self.resize(500, 600)
        self.setStyleSheet(get_dialog_stylesheet())
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Tab widget for different settings categories
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # IMAP Configuration Tab
        self._setup_imap_tab()
        
        # Application Preferences Tab
        self._setup_preferences_tab()
        
        # Connection test section
        self._setup_connection_test()
        layout.addWidget(self.test_frame)
        
        # Button box
        self._setup_buttons()
        layout.addWidget(self.button_frame)
    
    def _setup_imap_tab(self):
        """Set up the IMAP configuration tab."""
        imap_widget = QWidget()
        imap_layout = QVBoxLayout(imap_widget)
        
        # Server Settings Group
        server_group = QGroupBox("IMAP Server Settings")
        server_layout = QGridLayout(server_group)
        
        # Host
        server_layout.addWidget(QLabel("IMAP Host:"), 0, 0)
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("e.g., imap.gmail.com")
        server_layout.addWidget(self.host_edit, 0, 1)
        
        # Port
        server_layout.addWidget(QLabel("Port:"), 1, 0)
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(993)
        server_layout.addWidget(self.port_spin, 1, 1)
        
        # Use SSL
        self.ssl_check = QCheckBox("Use SSL/TLS (recommended)")
        self.ssl_check.setChecked(True)
        server_layout.addWidget(self.ssl_check, 2, 0, 1, 2)
        
        # Folder
        server_layout.addWidget(QLabel("Folder:"), 3, 0)
        self.folder_edit = QLineEdit()
        self.folder_edit.setText("INBOX")
        self.folder_edit.setPlaceholderText("INBOX")
        server_layout.addWidget(self.folder_edit, 3, 1)
        
        imap_layout.addWidget(server_group)
        
        # Authentication Group
        auth_group = QGroupBox("Authentication")
        auth_layout = QGridLayout(auth_group)
        
        # Username
        auth_layout.addWidget(QLabel("Username:"), 0, 0)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("your.email@example.com")
        auth_layout.addWidget(self.username_edit, 0, 1)
        
        # Password
        auth_layout.addWidget(QLabel("Password:"), 1, 0)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("App password or account password")
        auth_layout.addWidget(self.password_edit, 1, 1)
        
        # Storage method
        self.keyring_check = QCheckBox("Store credentials in system keyring (secure)")
        self.keyring_check.setChecked(True)
        auth_layout.addWidget(self.keyring_check, 2, 0, 1, 2)
        
        # Warning about .env storage
        warning_label = QLabel(
            "⚠️ If keyring is disabled, credentials will be stored in a .env file.\n"
            "This is less secure than keyring storage."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: #FFA500; font-size: 11px; margin-top: 8px;")
        auth_layout.addWidget(warning_label, 3, 0, 1, 2)
        
        imap_layout.addWidget(auth_group)
        
        # Gmail specific help
        help_group = QGroupBox("Gmail Setup Help")
        help_layout = QVBoxLayout(help_group)
        
        gmail_help = QLabel(
            "For Gmail users:\n"
            "1. Enable 2-factor authentication in your Google account\n"
            "2. Generate an App Password: Google Account → Security → 2-Step Verification → App passwords\n"
            "3. Use your Gmail address as username and the App Password as password\n"
            "4. IMAP Host: imap.gmail.com, Port: 993, SSL: Enabled"
        )
        gmail_help.setWordWrap(True)
        gmail_help.setStyleSheet("font-size: 11px; color: rgba(200, 200, 210, 255);")
        help_layout.addWidget(gmail_help)
        
        imap_layout.addWidget(help_group)
        
        imap_layout.addStretch()
        self.tab_widget.addTab(imap_widget, "IMAP Configuration")
    
    def _setup_preferences_tab(self):
        """Set up the application preferences tab."""
        prefs_widget = QWidget()
        prefs_layout = QVBoxLayout(prefs_widget)
        
        # Startup Group
        startup_group = QGroupBox("Startup Options")
        startup_layout = QVBoxLayout(startup_group)
        
        self.auto_refresh_check = QCheckBox("Automatically refresh emails on startup")
        self.auto_refresh_check.setChecked(True)
        startup_layout.addWidget(self.auto_refresh_check)
        
        prefs_layout.addWidget(startup_group)
        
        # Email Processing Group
        processing_group = QGroupBox("Email Processing")
        processing_layout = QGridLayout(processing_group)
        
        # Max emails to fetch
        processing_layout.addWidget(QLabel("Max emails to fetch:"), 0, 0)
        self.max_emails_spin = QSpinBox()
        self.max_emails_spin.setRange(1, 100)
        self.max_emails_spin.setValue(10)
        processing_layout.addWidget(self.max_emails_spin, 0, 1)
        
        # Summary sentences
        processing_layout.addWidget(QLabel("Summary sentences:"), 1, 0)
        self.summary_sentences_spin = QSpinBox()
        self.summary_sentences_spin.setRange(1, 10)
        self.summary_sentences_spin.setValue(3)
        processing_layout.addWidget(self.summary_sentences_spin, 1, 1)
        
        # Connection timeout
        processing_layout.addWidget(QLabel("Connection timeout (seconds):"), 2, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        processing_layout.addWidget(self.timeout_spin, 2, 1)
        
        prefs_layout.addWidget(processing_group)
        
        prefs_layout.addStretch()
        self.tab_widget.addTab(prefs_widget, "Preferences")
    
    def _setup_connection_test(self):
        """Set up the connection test section."""
        self.test_frame = QFrame()
        test_layout = QVBoxLayout(self.test_frame)
        test_layout.setContentsMargins(0, 8, 0, 0)
        
        # Test button
        button_layout = QHBoxLayout()
        self.test_button = QPushButton("🔗 Test Connection")
        self.test_button.setMinimumHeight(36)
        button_layout.addWidget(self.test_button)
        button_layout.addStretch()
        test_layout.addLayout(button_layout)
        
        # Progress bar
        self.test_progress = QProgressBar()
        self.test_progress.setVisible(False)
        self.test_progress.setRange(0, 0)  # Indeterminate
        test_layout.addWidget(self.test_progress)
        
        # Result display
        self.test_result = QTextEdit()
        self.test_result.setMaximumHeight(80)
        self.test_result.setVisible(False)
        self.test_result.setReadOnly(True)
        test_layout.addWidget(self.test_result)
    
    def _setup_buttons(self):
        """Set up the dialog buttons."""
        self.button_frame = QFrame()
        button_layout = QHBoxLayout(self.button_frame)
        button_layout.setContentsMargins(0, 8, 0, 0)
        
        # Load from .env button
        self.load_env_button = QPushButton("Load from .env")
        self.load_env_button.setToolTip("Load IMAP settings from .env file")
        button_layout.addWidget(self.load_env_button)
        
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.cancel_button)
        
        # Save button
        self.save_button = QPushButton("Save Settings")
        self.save_button.setDefault(True)
        button_layout.addWidget(self.save_button)
    
    def _setup_connections(self):
        """Set up signal connections."""
        self.test_button.clicked.connect(self._test_connection)
        self.load_env_button.clicked.connect(self._load_from_env)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._save_settings)
        
        # Enable/disable keyring checkbox based on availability
        try:
            import keyring
            keyring_available = True
        except ImportError:
            keyring_available = False
        
        if not keyring_available:
            self.keyring_check.setEnabled(False)
            self.keyring_check.setChecked(False)
            self.keyring_check.setText("Store credentials in system keyring (not available)")
    
    def _load_current_settings(self):
        """Load current settings into the form."""
        # IMAP settings
        self.host_edit.setText(self.current_settings.imap.host)
        self.port_spin.setValue(self.current_settings.imap.port)
        self.username_edit.setText(self.current_settings.imap.username)
        self.ssl_check.setChecked(self.current_settings.imap.use_ssl)
        self.folder_edit.setText(self.current_settings.imap.folder)
        
        # Preferences
        self.auto_refresh_check.setChecked(self.current_settings.auto_refresh_on_startup)
        self.keyring_check.setChecked(self.current_settings.use_keyring)
        self.max_emails_spin.setValue(self.current_settings.max_emails_to_fetch)
        self.summary_sentences_spin.setValue(self.current_settings.summary_sentences)
        self.timeout_spin.setValue(self.current_settings.connection_timeout)
        
        # Try to load password from keyring or .env
        self._load_stored_password()
    
    def _load_stored_password(self):
        """Load stored password from keyring or .env file."""
        username = self.username_edit.text()
        if not username:
            return
        
        password = None
        
        # Try keyring first if enabled
        if self.keyring_check.isChecked() and self.keyring_check.isEnabled():
            try:
                import keyring
                password = keyring.get_password("email-summarizer", username)
                if password:
                    logger.info("Password loaded from keyring")
            except Exception as e:
                logger.warning(f"Failed to load password from keyring: {e}")
        
        # Fallback to .env file
        if not password:
            try:
                load_dotenv()
                env_password = os.getenv("IMAP_PASSWORD")
                env_username = os.getenv("IMAP_USERNAME")
                if env_password and env_username == username:
                    password = env_password
                    logger.info("Password loaded from .env file")
            except Exception as e:
                logger.warning(f"Failed to load password from .env: {e}")
        
        if password:
            self.password_edit.setText(password)
    
    def _load_from_env(self):
        """Load settings from .env file."""
        try:
            load_dotenv()
            
            host = os.getenv("IMAP_HOST", "")
            port = int(os.getenv("IMAP_PORT", "993"))
            username = os.getenv("IMAP_USERNAME", "")
            password = os.getenv("IMAP_PASSWORD", "")
            
            if host:
                self.host_edit.setText(host)
            if port:
                self.port_spin.setValue(port)
            if username:
                self.username_edit.setText(username)
            if password:
                self.password_edit.setText(password)
            
            # Show success message
            if any([host, username, password]):
                QMessageBox.information(
                    self, 
                    "Settings Loaded", 
                    "IMAP settings have been loaded from .env file."
                )
            else:
                QMessageBox.warning(
                    self, 
                    "No Settings Found", 
                    "No IMAP settings found in .env file."
                )
                
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error Loading Settings", 
                f"Failed to load settings from .env file:\n{str(e)}"
            )
    
    def _test_connection(self):
        """Test the IMAP connection with current settings."""
        # Validate required fields
        if not self.host_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter IMAP host.")
            return
        
        if not self.username_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter username.")
            return
        
        if not self.password_edit.text():
            QMessageBox.warning(self, "Missing Information", "Please enter password.")
            return
        
        # Create config from current form data
        config = ImapConfig(
            host=self.host_edit.text().strip(),
            port=self.port_spin.value(),
            username=self.username_edit.text().strip(),
            password=self.password_edit.text(),
            use_ssl=self.ssl_check.isChecked(),
            folder=self.folder_edit.text().strip() or "INBOX"
        )
        
        # Start connection test
        self.test_controller.test_connection(config)
    
    def _on_test_started(self):
        """Handle connection test start."""
        self.test_button.setText("Testing...")
        self.test_button.setEnabled(False)
        self.test_progress.setVisible(True)
        self.test_result.setVisible(False)
    
    def _on_test_completed(self, success: bool, message: str):
        """Handle connection test completion."""
        self.test_button.setText("🔗 Test Connection")
        self.test_button.setEnabled(True)
        self.test_progress.setVisible(False)
        
        # Show result
        self.test_result.setVisible(True)
        if success:
            self.test_result.setStyleSheet("color: #4CAF50; background-color: rgba(76, 175, 80, 0.1);")
            self.test_result.setText(f"✅ Success: {message}")
        else:
            self.test_result.setStyleSheet("color: #F44336; background-color: rgba(244, 67, 54, 0.1);")
            self.test_result.setText(f"❌ Failed: {message}")
    
    def _save_settings(self):
        """Save settings and close dialog."""
        # Validate required fields
        if not self.host_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter IMAP host.")
            self.tab_widget.setCurrentIndex(0)  # Switch to IMAP tab
            self.host_edit.setFocus()
            return
        
        if not self.username_edit.text().strip():
            QMessageBox.warning(self, "Missing Information", "Please enter username.")
            self.tab_widget.setCurrentIndex(0)
            self.username_edit.setFocus()
            return
        
        if not self.password_edit.text():
            QMessageBox.warning(self, "Missing Information", "Please enter password.")
            self.tab_widget.setCurrentIndex(0)
            self.password_edit.setFocus()
            return
        
        try:
            # Create settings object
            imap_config = ImapConfig(
                host=self.host_edit.text().strip(),
                port=self.port_spin.value(),
                username=self.username_edit.text().strip(),
                password=self.password_edit.text(),
                use_ssl=self.ssl_check.isChecked(),
                folder=self.folder_edit.text().strip() or "INBOX"
            )
            
            settings = AppSettings(
                imap=imap_config,
                auto_refresh_on_startup=self.auto_refresh_check.isChecked(),
                use_keyring=self.keyring_check.isChecked() and self.keyring_check.isEnabled(),
                max_emails_to_fetch=self.max_emails_spin.value(),
                summary_sentences=self.summary_sentences_spin.value(),
                connection_timeout=self.timeout_spin.value()
            )
            
            # Store credentials
            self._store_credentials(settings)
            
            # Emit signal and close
            self.settings_saved.emit(settings)
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Error Saving Settings", 
                f"Failed to save settings:\n{str(e)}"
            )
    
    def _store_credentials(self, settings: AppSettings):
        """Store credentials using the selected method."""
        username = settings.imap.username
        password = settings.imap.password
        
        if settings.use_keyring:
            try:
                import keyring
                keyring.set_password("email-summarizer", username, password)
                logger.info("Credentials stored in keyring")
                return
            except Exception as e:
                logger.warning(f"Failed to store credentials in keyring: {e}")
                # Fall back to .env storage
        
        # Store in .env file as fallback
        try:
            env_file = ".env"
            
            # Update .env file
            set_key(env_file, "IMAP_HOST", settings.imap.host)
            set_key(env_file, "IMAP_PORT", str(settings.imap.port))
            set_key(env_file, "IMAP_USERNAME", username)
            set_key(env_file, "IMAP_PASSWORD", password)
            
            logger.info("Credentials stored in .env file")
            
            if settings.use_keyring:  # Show warning if keyring was preferred but failed
                QMessageBox.warning(
                    self,
                    "Keyring Storage Failed",
                    "Could not store credentials in system keyring. "
                    "Credentials have been saved to .env file instead. "
                    "Please ensure this file is kept secure and not shared."
                )
                
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            QMessageBox.critical(
                self,
                "Storage Error",
                f"Failed to store credentials:\n{str(e)}"
            )
    
    @staticmethod
    def load_settings() -> AppSettings:
        """Load settings from storage (keyring or .env)."""
        try:
            load_dotenv()
            
            # Load basic settings from .env
            host = os.getenv("IMAP_HOST", "")
            port = int(os.getenv("IMAP_PORT", "993"))
            username = os.getenv("IMAP_USERNAME", "")
            
            password = ""
            use_keyring = True
            
            # Try to load password from keyring first
            if username:
                try:
                    import keyring
                    stored_password = keyring.get_password("email-summarizer", username)
                    if stored_password:
                        password = stored_password
                        logger.info("Password loaded from keyring")
                except Exception as e:
                    logger.warning(f"Failed to load from keyring: {e}")
                    use_keyring = False
            
            # Fallback to .env password
            if not password:
                password = os.getenv("IMAP_PASSWORD", "")
                use_keyring = False
                if password:
                    logger.info("Password loaded from .env file")
            
            return AppSettings(
                imap=ImapConfig(
                    host=host,
                    port=port,
                    username=username,
                    password=password
                ),
                use_keyring=use_keyring
            )
            
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
            return AppSettings(
                imap=ImapConfig(host="", port=993, username="", password="")
            )