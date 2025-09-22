"""
Email Summarizer - Main Application Entry Point

A local, privacy-focused email summarizer that connects to IMAP servers
and generates summaries using local TextRank algorithm.
"""
import sys
import os
import logging
from pathlib import Path
from typing import Optional

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont

from models import AppSettings
from theming import apply_dark_theme
from ui_main import MainWindow
from ui_settings import SettingsDialog
from utils import sanitize_filename


# Application metadata
APP_NAME = "Email Summarizer"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Email Summarizer Team"
APP_DESCRIPTION = "Local email summarizer with TextRank algorithm"


def setup_logging() -> None:
    """Set up application logging."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_file = log_dir / "email_summarizer.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set more verbose logging for our modules
    logging.getLogger('app').setLevel(logging.DEBUG)
    
    # Reduce noise from external libraries
    logging.getLogger('sumy').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")


def create_splash_screen(app: QApplication) -> QSplashScreen:
    """
    Create a splash screen for the application.
    
    Args:
        app: QApplication instance
        
    Returns:
        QSplashScreen instance
    """
    # Create a simple splash screen
    pixmap = QPixmap(400, 200)
    pixmap.fill(QColor(35, 35, 40))  # Dark background
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Title
    title_font = QFont("Arial", 24, QFont.Bold)
    painter.setFont(title_font)
    painter.setPen(QColor(240, 240, 245))
    painter.drawText(pixmap.rect(), Qt.AlignCenter | Qt.AlignTop, "📧 Email Summarizer")
    
    # Version
    version_font = QFont("Arial", 12)
    painter.setFont(version_font)
    painter.setPen(QColor(180, 180, 190))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, f"Version {APP_VERSION}")
    
    # Loading text
    loading_font = QFont("Arial", 10)
    painter.setFont(loading_font)
    painter.setPen(QColor(138, 43, 226))  # Violet accent
    painter.drawText(pixmap.rect(), Qt.AlignCenter | Qt.AlignBottom, "Initializing...")
    
    painter.end()
    
    splash = QSplashScreen(pixmap)
    splash.setAttribute(Qt.WA_DeleteOnClose)
    return splash


def load_application_settings() -> AppSettings:
    """
    Load application settings from storage.
    
    Returns:
        AppSettings instance
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Try to load from settings dialog's static method
        settings = SettingsDialog.load_settings()
        
        if settings.imap.is_complete():
            logger.info("Loaded complete IMAP settings")
        else:
            logger.info("IMAP settings incomplete, user will need to configure")
        
        return settings
        
    except Exception as e:
        logger.warning(f"Failed to load settings: {e}")
        # Return default settings
        from models import ImapConfig
        return AppSettings(
            imap=ImapConfig(host="", port=993, username="", password="")
        )


def check_dependencies() -> tuple[bool, str]:
    """
    Check if all required dependencies are available.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    missing_deps = []
    
    try:
        import sumy
    except ImportError:
        missing_deps.append("sumy (text summarization)")
    
    try:
        import beautifulsoup4
    except ImportError:
        missing_deps.append("beautifulsoup4 (HTML parsing)")
    
    try:
        import keyring
    except ImportError:
        # Keyring is optional
        pass
    
    try:
        import dotenv
    except ImportError:
        missing_deps.append("python-dotenv (configuration)")
    
    if missing_deps:
        return False, f"Missing dependencies: {', '.join(missing_deps)}"
    
    return True, "All dependencies available"


def show_first_run_dialog(parent=None) -> bool:
    """
    Show first-run dialog explaining the application.
    
    Args:
        parent: Parent widget for dialog
        
    Returns:
        True if user wants to continue, False to exit
    """
    welcome_text = f"""
<h2>Welcome to Email Summarizer!</h2>

<p>This application helps you quickly understand your emails by generating 
local summaries using the TextRank algorithm.</p>

<h3>Key Features:</h3>
<ul>
<li><b>Privacy-focused:</b> All processing happens locally on your machine</li>
<li><b>Secure:</b> IMAP connections use SSL/TLS encryption</li>
<li><b>No cloud services:</b> No data is sent to external servers</li>
<li><b>Local summarization:</b> Uses TextRank algorithm for text summarization</li>
</ul>

<h3>Getting Started:</h3>
<ol>
<li>Configure your IMAP email settings in the Settings dialog</li>
<li>For Gmail: Enable 2FA and generate an App Password</li>
<li>Click Refresh to fetch and summarize your latest emails</li>
</ol>

<p><b>Note:</b> Your credentials are stored securely in your system keyring 
when possible, or in a local .env file.</p>

<p>Would you like to configure your email settings now?</p>
"""
    
    reply = QMessageBox.question(
        parent,
        f"{APP_NAME} - Welcome",
        welcome_text,
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.Yes
    )
    
    return reply == QMessageBox.Yes


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Global exception handler for uncaught exceptions.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Handle Ctrl+C gracefully
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    # Show error dialog if QApplication exists
    try:
        app = QApplication.instance()
        if app:
            QMessageBox.critical(
                None,
                "Application Error",
                f"An unexpected error occurred:\n\n{exc_type.__name__}: {exc_value}\n\n"
                "Please check the log file for more details."
            )
    except:
        pass  # Ignore any errors in error handling


def main() -> int:
    """
    Main application entry point.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Set up logging first
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Set up global exception handler
    sys.excepthook = handle_exception
    
    try:
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        app.setOrganizationName(APP_AUTHOR)
        app.setApplicationDisplayName("📧 Email Summarizer")
        
        # Apply dark theme
        apply_dark_theme(app)
        
        # Check dependencies
        deps_ok, deps_message = check_dependencies()
        if not deps_ok:
            QMessageBox.critical(
                None,
                "Missing Dependencies",
                f"Required dependencies are missing:\n\n{deps_message}\n\n"
                "Please install them using:\n"
                "pip install -r requirements.txt"
            )
            return 1
        
        # Show splash screen
        splash = create_splash_screen(app)
        splash.show()
        app.processEvents()
        
        # Load application settings
        splash.showMessage("Loading settings...", Qt.AlignBottom | Qt.AlignCenter, QColor(138, 43, 226))
        app.processEvents()
        
        settings = load_application_settings()
        
        # Check if this is the first run (no settings configured)
        is_first_run = not settings.imap.is_complete()
        
        # Initialize main window
        splash.showMessage("Initializing interface...", Qt.AlignBottom | Qt.AlignCenter, QColor(138, 43, 226))
        app.processEvents()
        
        main_window = MainWindow(settings)
        
        # Show main window
        splash.finish(main_window)
        main_window.show()
        
        # Handle first run
        if is_first_run:
            # Small delay to let the main window fully appear
            def show_first_run():
                if show_first_run_dialog(main_window):
                    main_window._show_settings()
            
            QTimer.singleShot(500, show_first_run)
        
        logger.info("Application started successfully")
        
        # Run the application
        return app.exec()
        
    except ImportError as e:
        error_msg = f"Failed to import required module: {e}"
        logger.error(error_msg)
        
        try:
            QMessageBox.critical(
                None,
                "Import Error",
                f"{error_msg}\n\nPlease install requirements:\n"
                "pip install -r requirements.txt"
            )
        except:
            print(f"Error: {error_msg}")
        
        return 1
        
    except Exception as e:
        error_msg = f"Failed to start application: {e}"
        logger.error(error_msg, exc_info=True)
        
        try:
            QMessageBox.critical(
                None,
                "Startup Error", 
                error_msg
            )
        except:
            print(f"Error: {error_msg}")
        
        return 1


def cli_mode():
    """
    Command-line interface for the application (future feature).
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description=APP_DESCRIPTION,
        prog="email-summarizer"
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version=f"{APP_NAME} {APP_VERSION}"
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch GUI interface (default)"
    )
    
    parser.add_argument(
        "--config",
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level"
    )
    
    args = parser.parse_args()
    
    # Set log level if specified
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # For now, always launch GUI
    return main()


if __name__ == "__main__":
    # Check if running as CLI or GUI
    if len(sys.argv) > 1 and "--help" in sys.argv:
        exit_code = cli_mode()
    else:
        exit_code = main()
    
    sys.exit(exit_code)