"""
Email Summarizer Application Package

A local, privacy-focused email summarizer that connects to IMAP servers
and generates summaries using local TextRank algorithm.
"""

__version__ = "1.0.0"
__author__ = "Email Summarizer Team"
__description__ = "Local email summarizer with TextRank algorithm"

# Main application components
from .main import main, APP_NAME, APP_VERSION
from .models import EmailItem, ImapConfig, AppSettings
from .ui_main import MainWindow
from .ui_settings import SettingsDialog

__all__ = [
    'main',
    'APP_NAME', 
    'APP_VERSION',
    'EmailItem',
    'ImapConfig', 
    'AppSettings',
    'MainWindow',
    'SettingsDialog'
]