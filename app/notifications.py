"""
Desktop notification support for new emails.
"""
import logging
import sys
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages desktop notifications for new emails."""
    
    def __init__(self, app_name: str = "Email Summarizer"):
        """
        Initialize notification manager.
        
        Args:
            app_name: Application name to display in notifications
        """
        self.app_name = app_name
        self.enabled = self._check_platform_support()
        
        if self.enabled and sys.platform == 'win32':
            try:
                from winotify import Notification
                self.Notification = Notification
            except ImportError:
                logger.warning("winotify not available, notifications disabled")
                self.enabled = False
    
    def _check_platform_support(self) -> bool:
        """Check if notifications are supported on this platform."""
        if sys.platform == 'win32':
            try:
                import winotify
                return True
            except ImportError:
                return False
        elif sys.platform == 'darwin':
            # macOS support could be added with osascript
            return False
        elif sys.platform.startswith('linux'):
            # Linux support could be added with notify-send
            return False
        return False
    
    def show_new_email_notification(
        self,
        sender: str,
        subject: str,
        summary: Optional[str] = None,
        count: int = 1
    ):
        """
        Show notification for new email(s).
        
        Args:
            sender: Email sender name/address
            subject: Email subject
            summary: Email summary (optional)
            count: Number of new emails
        """
        if not self.enabled:
            return
        
        try:
            if sys.platform == 'win32':
                self._show_windows_notification(sender, subject, summary, count)
        except Exception as e:
            logger.warning(f"Failed to show notification: {e}")
    
    def _show_windows_notification(
        self,
        sender: str,
        subject: str,
        summary: Optional[str],
        count: int
    ):
        """Show Windows toast notification."""
        if count == 1:
            title = f"New Email from {sender}"
            message = subject
            if summary:
                message += f"\n\n{summary[:100]}..."
        else:
            title = f"{count} New Emails"
            message = f"Latest: {subject}"
        
        try:
            toast = self.Notification(
                app_id=self.app_name,
                title=title,
                msg=message,
                duration="short"
            )
            toast.show()
        except Exception as e:
            logger.debug(f"Windows notification error: {e}")
    
    def show_error_notification(self, error_message: str):
        """
        Show error notification.
        
        Args:
            error_message: Error message to display
        """
        if not self.enabled:
            return
        
        try:
            if sys.platform == 'win32':
                toast = self.Notification(
                    app_id=self.app_name,
                    title="Email Summarizer Error",
                    msg=error_message,
                    duration="short"
                )
                toast.show()
        except Exception as e:
            logger.debug(f"Failed to show error notification: {e}")
    
    def show_success_notification(self, message: str):
        """
        Show success notification.
        
        Args:
            message: Success message to display
        """
        if not self.enabled:
            return
        
        try:
            if sys.platform == 'win32':
                toast = self.Notification(
                    app_id=self.app_name,
                    title="Email Summarizer",
                    msg=message,
                    duration="short"
                )
                toast.show()
        except Exception as e:
            logger.debug(f"Failed to show success notification: {e}")


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get or create the global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
