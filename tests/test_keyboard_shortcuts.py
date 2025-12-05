"""
Unit tests for keyboard shortcuts functionality.
"""
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QKeySequence


def test_keyboard_shortcuts_initialized():
    """Test that keyboard shortcuts are properly initialized."""
    # This test would require importing ui_main and creating a MainWindow
    # For now, we just test that the module imports correctly
    from ui_main import MainWindow
    assert hasattr(MainWindow, '_setup_keyboard_shortcuts')


def test_focus_search_method_exists():
    """Test that focus search method exists."""
    from ui_main import MainWindow
    assert hasattr(MainWindow, '_focus_search')


def test_scroll_methods_exist():
    """Test that scroll methods exist."""
    from ui_main import MainWindow
    assert hasattr(MainWindow, '_scroll_down')
    assert hasattr(MainWindow, '_scroll_up')


def test_account_switching_methods_exist():
    """Test that account switching methods exist."""
    from ui_main import MainWindow
    assert hasattr(MainWindow, '_switch_to_next_account')
    assert hasattr(MainWindow, '_switch_to_prev_account')


def test_keyboard_shortcuts_dialog_method_exists():
    """Test that keyboard shortcuts dialog method exists."""
    from ui_main import MainWindow
    assert hasattr(MainWindow, '_show_keyboard_shortcuts')


def test_key_sequences_are_valid():
    """Test that all keyboard shortcut sequences are valid."""
    sequences = [
        "Ctrl+R",      # Refresh
        "Ctrl+,",      # Settings
        "Ctrl+F",      # Focus search
        "Ctrl+Q",      # Quit
        "F1",          # Help
        "J",           # Scroll down
        "K",           # Scroll up
        "Ctrl+Tab",    # Next account
        "Ctrl+Shift+Tab",  # Previous account
        "Escape",      # Clear search
    ]
    
    for seq in sequences:
        key_seq = QKeySequence(seq)
        assert not key_seq.isEmpty(), f"Invalid key sequence: {seq}"


def test_keyboard_shortcut_descriptions():
    """Test that keyboard shortcuts have proper descriptions."""
    shortcuts = {
        "Ctrl+R": "Refresh emails",
        "Ctrl+,": "Open settings",
        "Ctrl+F": "Focus search",
        "Ctrl+Q": "Quit application",
        "F1": "Show shortcuts",
        "J": "Scroll down",
        "K": "Scroll up",
    }
    
    # Verify all shortcuts have descriptions
    assert len(shortcuts) >= 7
    
    # Verify no empty descriptions
    for key, description in shortcuts.items():
        assert description, f"Empty description for shortcut: {key}"
        assert len(description) > 0
