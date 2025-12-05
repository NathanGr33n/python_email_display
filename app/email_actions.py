"""
Email action workers for background operations.
"""
import logging
from PySide6.QtCore import QObject, Signal, QRunnable, Slot

from imap_client import ImapClient
from models import ImapConfig

logger = logging.getLogger(__name__)


class EmailActionSignals(QObject):
    """Signals for email action worker."""
    finished = Signal(bool, str)  # success, message
    error = Signal(str)


class EmailActionWorker(QRunnable):
    """Worker for performing email actions in background."""
    
    def __init__(self, config: ImapConfig, action: str, message_id: str, **kwargs):
        """
        Initialize email action worker.
        
        Args:
            config: IMAP configuration
            action: Action to perform ('mark_read', 'mark_unread', 'delete', 'move')
            message_id: Message ID to act on
            **kwargs: Additional arguments (e.g., destination_folder for move)
        """
        super().__init__()
        self.config = config
        self.action = action
        self.message_id = message_id
        self.kwargs = kwargs
        self.signals = EmailActionSignals()
    
    @Slot()
    def run(self):
        """Execute the email action."""
        try:
            with ImapClient(self.config) as client:
                if self.action == 'mark_read':
                    success = client.mark_as_read(self.message_id)
                    message = "Marked as read" if success else "Failed to mark as read"
                
                elif self.action == 'mark_unread':
                    success = client.mark_as_unread(self.message_id)
                    message = "Marked as unread" if success else "Failed to mark as unread"
                
                elif self.action == 'delete':
                    success = client.delete_message(self.message_id)
                    message = "Deleted successfully" if success else "Failed to delete"
                
                elif self.action == 'move':
                    destination = self.kwargs.get('destination_folder', 'Archive')
                    success = client.move_to_folder(self.message_id, destination)
                    message = f"Moved to {destination}" if success else f"Failed to move to {destination}"
                
                else:
                    success = False
                    message = f"Unknown action: {self.action}"
                
                self.signals.finished.emit(success, message)
                
        except Exception as e:
            logger.error(f"Email action failed: {e}")
            self.signals.error.emit(str(e))
            self.signals.finished.emit(False, str(e))
