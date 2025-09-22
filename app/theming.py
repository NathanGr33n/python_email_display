"""
Dark theme configuration and styling for the Email Summarizer application.
"""
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt


def apply_dark_theme(app: QApplication) -> None:
    """
    Apply a custom dark theme to the application.
    
    Args:
        app: QApplication instance
    """
    # Try to use qdarktheme if available
    try:
        import qdarktheme
        qdarktheme.setup_theme("dark")
        return
    except ImportError:
        pass
    
    # Fallback: Custom dark palette
    palette = QPalette()
    
    # Color scheme
    dark_bg = QColor(35, 35, 40)        # Main background
    darker_bg = QColor(25, 25, 30)      # Darker areas
    light_bg = QColor(50, 50, 60)       # Input/widget backgrounds
    text_color = QColor(240, 240, 245)  # Primary text
    disabled_text = QColor(120, 120, 125)  # Disabled text
    accent_color = QColor(138, 43, 226)  # Violet accent
    accent_hover = QColor(148, 63, 236)  # Lighter violet for hover
    border_color = QColor(70, 70, 80)    # Borders and separators
    
    # Set palette colors
    palette.setColor(QPalette.Window, dark_bg)
    palette.setColor(QPalette.WindowText, text_color)
    palette.setColor(QPalette.Base, light_bg)
    palette.setColor(QPalette.AlternateBase, darker_bg)
    palette.setColor(QPalette.ToolTipBase, darker_bg)
    palette.setColor(QPalette.ToolTipText, text_color)
    palette.setColor(QPalette.Text, text_color)
    palette.setColor(QPalette.Button, light_bg)
    palette.setColor(QPalette.ButtonText, text_color)
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, accent_color)
    palette.setColor(QPalette.Highlight, accent_color)
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    
    # Disabled states
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_text)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_text)
    
    app.setPalette(palette)


def get_email_card_stylesheet() -> str:
    """
    Get stylesheet for email cards with hover effects.
    
    Returns:
        CSS stylesheet string
    """
    return """
        QWidget#email_card {
            background-color: rgba(50, 50, 60, 255);
            border: 1px solid rgba(70, 70, 80, 255);
            border-radius: 8px;
            padding: 0px;
            margin: 4px;
        }
        
        QWidget#email_card:hover {
            background-color: rgba(60, 60, 70, 255);
            border-color: rgba(138, 43, 226, 128);
        }
        
        QLabel#sender_label {
            color: rgba(240, 240, 245, 255);
            font-size: 13px;
            font-weight: normal;
            padding: 2px;
        }
        
        QLabel#subject_label {
            color: rgba(240, 240, 245, 255);
            font-size: 14px;
            font-weight: bold;
            padding: 2px;
        }
        
        QLabel#date_label {
            color: rgba(180, 180, 190, 255);
            font-size: 12px;
            padding: 2px;
        }
        
        QLabel#summary_label {
            color: rgba(200, 200, 210, 255);
            font-size: 12px;
            line-height: 1.4;
            padding: 2px;
        }
    """


def get_toolbar_stylesheet() -> str:
    """
    Get stylesheet for the toolbar.
    
    Returns:
        CSS stylesheet string
    """
    return """
        QToolBar {
            background-color: rgba(25, 25, 30, 255);
            border: none;
            border-bottom: 1px solid rgba(70, 70, 80, 255);
            spacing: 8px;
            padding: 4px;
        }
        
        QToolButton {
            background-color: rgba(50, 50, 60, 255);
            border: 1px solid rgba(70, 70, 80, 255);
            border-radius: 6px;
            padding: 6px 12px;
            margin: 2px;
            color: rgba(240, 240, 245, 255);
            font-size: 13px;
        }
        
        QToolButton:hover {
            background-color: rgba(138, 43, 226, 255);
            border-color: rgba(148, 63, 236, 255);
        }
        
        QToolButton:pressed {
            background-color: rgba(118, 33, 206, 255);
        }
        
        QToolButton:disabled {
            background-color: rgba(40, 40, 50, 255);
            color: rgba(120, 120, 125, 255);
            border-color: rgba(60, 60, 70, 255);
        }
    """


def get_scroll_area_stylesheet() -> str:
    """
    Get stylesheet for scroll areas.
    
    Returns:
        CSS stylesheet string
    """
    return """
        QScrollArea {
            background-color: rgba(35, 35, 40, 255);
            border: none;
        }
        
        QScrollArea > QWidget > QWidget {
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            background-color: rgba(50, 50, 60, 255);
            width: 12px;
            border: none;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background-color: rgba(100, 100, 120, 255);
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: rgba(138, 43, 226, 255);
        }
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            background: transparent;
            height: 0px;
        }
        
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            background: transparent;
        }
    """


def get_dialog_stylesheet() -> str:
    """
    Get stylesheet for dialogs and settings windows.
    
    Returns:
        CSS stylesheet string
    """
    return """
        QDialog {
            background-color: rgba(35, 35, 40, 255);
            color: rgba(240, 240, 245, 255);
        }
        
        QGroupBox {
            background-color: rgba(45, 45, 55, 255);
            border: 1px solid rgba(70, 70, 80, 255);
            border-radius: 6px;
            margin-top: 6px;
            padding-top: 6px;
            font-weight: bold;
            color: rgba(240, 240, 245, 255);
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: rgba(138, 43, 226, 255);
        }
        
        QLineEdit {
            background-color: rgba(60, 60, 70, 255);
            border: 1px solid rgba(80, 80, 90, 255);
            border-radius: 4px;
            padding: 6px;
            color: rgba(240, 240, 245, 255);
            font-size: 13px;
        }
        
        QLineEdit:focus {
            border-color: rgba(138, 43, 226, 255);
        }
        
        QSpinBox {
            background-color: rgba(60, 60, 70, 255);
            border: 1px solid rgba(80, 80, 90, 255);
            border-radius: 4px;
            padding: 4px;
            color: rgba(240, 240, 245, 255);
        }
        
        QSpinBox:focus {
            border-color: rgba(138, 43, 226, 255);
        }
        
        QCheckBox {
            color: rgba(240, 240, 245, 255);
            spacing: 6px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid rgba(80, 80, 90, 255);
            border-radius: 3px;
            background-color: rgba(60, 60, 70, 255);
        }
        
        QCheckBox::indicator:checked {
            background-color: rgba(138, 43, 226, 255);
            border-color: rgba(148, 63, 236, 255);
        }
        
        QCheckBox::indicator:checked::before {
            content: "✓";
            color: white;
            font-weight: bold;
        }
        
        QPushButton {
            background-color: rgba(50, 50, 60, 255);
            border: 1px solid rgba(80, 80, 90, 255);
            border-radius: 6px;
            padding: 8px 16px;
            color: rgba(240, 240, 245, 255);
            font-size: 13px;
            font-weight: normal;
        }
        
        QPushButton:hover {
            background-color: rgba(138, 43, 226, 255);
            border-color: rgba(148, 63, 236, 255);
        }
        
        QPushButton:pressed {
            background-color: rgba(118, 33, 206, 255);
        }
        
        QPushButton:disabled {
            background-color: rgba(40, 40, 50, 255);
            color: rgba(120, 120, 125, 255);
            border-color: rgba(60, 60, 70, 255);
        }
        
        QLabel {
            color: rgba(240, 240, 245, 255);
        }
        
        QTextEdit {
            background-color: rgba(60, 60, 70, 255);
            border: 1px solid rgba(80, 80, 90, 255);
            border-radius: 4px;
            padding: 6px;
            color: rgba(240, 240, 245, 255);
            selection-background-color: rgba(138, 43, 226, 128);
        }
    """


def get_loading_stylesheet() -> str:
    """
    Get stylesheet for loading indicators.
    
    Returns:
        CSS stylesheet string
    """
    return """
        QProgressBar {
            background-color: rgba(60, 60, 70, 255);
            border: 1px solid rgba(80, 80, 90, 255);
            border-radius: 4px;
            text-align: center;
            color: rgba(240, 240, 245, 255);
        }
        
        QProgressBar::chunk {
            background-color: rgba(138, 43, 226, 255);
            border-radius: 3px;
            margin: 1px;
        }
    """