"""
Qt worker threads for non-blocking operations.

Handles IMAP email fetching and text summarization in background threads
to keep the UI responsive.
"""
import logging
from typing import List, Optional, Tuple
from PySide6.QtCore import QThread, Signal, QObject, QRunnable, QThreadPool
from PySide6.QtWidgets import QApplication

from models import EmailItem, ImapConfig
from imap_client import ImapClient, ImapClientError, AuthenticationError, ConnectionError
from summarizer import get_summarizer


logger = logging.getLogger(__name__)


class EmailFetchWorker(QThread):
    """
    Worker thread for fetching emails from IMAP server.
    
    Emits signals for progress updates and completion.
    """
    
    # Signals
    progress_updated = Signal(str)  # Status message
    emails_fetched = Signal(list)   # List[EmailItem] - successfully fetched emails
    error_occurred = Signal(str)    # Error message
    finished = Signal()             # Operation completed
    
    def __init__(self, config: ImapConfig, email_count: int = 10, parent=None):
        """
        Initialize email fetch worker.
        
        Args:
            config: IMAP configuration
            email_count: Number of emails to fetch
            parent: Parent QObject
        """
        super().__init__(parent)
        self.config = config
        self.email_count = email_count
        self._should_stop = False
    
    def stop(self):
        """Request the worker to stop gracefully."""
        self._should_stop = True
    
    def run(self):
        """Main worker thread function."""
        try:
            self.progress_updated.emit("Connecting to email server...")
            
            # Check if we should stop
            if self._should_stop:
                return
            
            # Create IMAP client and connect
            with ImapClient(self.config, timeout=30) as client:
                self.progress_updated.emit("Connected! Fetching emails...")
                
                if self._should_stop:
                    return
                
                # Fetch emails
                emails = client.fetch_latest_emails(self.email_count)
                
                if self._should_stop:
                    return
                
                if not emails:
                    self.progress_updated.emit("No emails found in inbox")
                    self.emails_fetched.emit([])
                else:
                    self.progress_updated.emit(f"Fetched {len(emails)} emails. Generating summaries...")
                    
                    # Generate summaries for each email
                    summarized_emails = []
                    summarizer = get_summarizer()
                    
                    for i, email in enumerate(emails):
                        if self._should_stop:
                            return
                        
                        # Update progress
                        self.progress_updated.emit(f"Summarizing email {i+1}/{len(emails)}")
                        
                        # Generate summary if not already present
                        if not email.summary:
                            try:
                                email.summary = summarizer.summarize(email.body_text)
                            except Exception as e:
                                logger.warning(f"Failed to summarize email {i+1}: {e}")
                                email.summary = "Summary generation failed."
                        
                        summarized_emails.append(email)
                        
                        # Process events to keep UI responsive
                        QApplication.processEvents()
                    
                    if not self._should_stop:
                        self.emails_fetched.emit(summarized_emails)
                        self.progress_updated.emit(f"Successfully loaded {len(summarized_emails)} emails")
                
        except AuthenticationError as e:
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        except ConnectionError as e:
            error_msg = f"Connection failed: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        except ImapClientError as e:
            error_msg = f"Email fetch failed: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self.finished.emit()


class ConnectionTestWorker(QThread):
    """
    Worker thread for testing IMAP connection.
    
    Quick test without fetching emails.
    """
    
    # Signals
    test_completed = Signal(bool, str)  # (success, message)
    finished = Signal()
    
    def __init__(self, config: ImapConfig, parent=None):
        """
        Initialize connection test worker.
        
        Args:
            config: IMAP configuration
            parent: Parent QObject
        """
        super().__init__(parent)
        self.config = config
        self._should_stop = False
    
    def stop(self):
        """Request the worker to stop gracefully."""
        self._should_stop = True
    
    def run(self):
        """Test IMAP connection."""
        try:
            if self._should_stop:
                return
            
            client = ImapClient(self.config, timeout=15)  # Shorter timeout for test
            success, message = client.test_connection()
            
            if not self._should_stop:
                self.test_completed.emit(success, message)
                
        except Exception as e:
            if not self._should_stop:
                error_msg = f"Connection test failed: {str(e)}"
                logger.error(error_msg)
                self.test_completed.emit(False, error_msg)
        finally:
            self.finished.emit()


class SummaryWorkerSignals(QObject):
    """
    Signals for summary generation worker.
    
    QRunnable doesn't support signals directly, so we use a separate QObject.
    """
    summary_generated = Signal(int, str)  # (email_index, summary)
    error_occurred = Signal(int, str)     # (email_index, error_message)


class SummaryGenerationWorker(QRunnable):
    """
    Runnable worker for generating email summaries.
    
    Used with QThreadPool for parallel summary generation.
    """
    
    def __init__(self, email_index: int, email_text: str, max_sentences: int = 3):
        """
        Initialize summary worker.
        
        Args:
            email_index: Index of email in the list
            email_text: Email body text
            max_sentences: Maximum sentences in summary
        """
        super().__init__()
        self.email_index = email_index
        self.email_text = email_text
        self.max_sentences = max_sentences
        self.signals = SummaryWorkerSignals()
        self.setAutoDelete(True)
    
    def run(self):
        """Generate summary for the email."""
        try:
            summarizer = get_summarizer()
            summarizer.max_sentences = self.max_sentences
            summary = summarizer.summarize(self.email_text)
            self.signals.summary_generated.emit(self.email_index, summary)
        except Exception as e:
            error_msg = f"Summary generation failed: {str(e)}"
            logger.warning(f"Failed to summarize email {self.email_index}: {e}")
            self.signals.error_occurred.emit(self.email_index, error_msg)


class EmailRefreshController(QObject):
    """
    Controller for coordinating email refresh operations.
    
    Manages the workflow of fetching emails and generating summaries.
    """
    
    # Signals
    refresh_started = Signal()
    progress_updated = Signal(str)
    emails_updated = Signal(list)  # List[EmailItem]
    refresh_completed = Signal(bool, str)  # (success, message)
    
    def __init__(self, parent=None):
        """Initialize the refresh controller."""
        super().__init__(parent)
        self._current_worker: Optional[EmailFetchWorker] = None
        self._is_refreshing = False
    
    def is_refreshing(self) -> bool:
        """Check if refresh operation is in progress."""
        return self._is_refreshing
    
    def start_refresh(self, config: ImapConfig, email_count: int = 10):
        """
        Start email refresh operation.
        
        Args:
            config: IMAP configuration
            email_count: Number of emails to fetch
        """
        if self._is_refreshing:
            logger.warning("Refresh already in progress, ignoring request")
            return
        
        if not config.is_complete():
            self.refresh_completed.emit(False, "IMAP configuration is incomplete")
            return
        
        self._is_refreshing = True
        self.refresh_started.emit()
        
        # Create and configure worker
        self._current_worker = EmailFetchWorker(config, email_count)
        
        # Connect signals
        self._current_worker.progress_updated.connect(self.progress_updated.emit)
        self._current_worker.emails_fetched.connect(self._on_emails_fetched)
        self._current_worker.error_occurred.connect(self._on_error)
        self._current_worker.finished.connect(self._on_finished)
        
        # Start worker
        self._current_worker.start()
    
    def cancel_refresh(self):
        """Cancel current refresh operation."""
        if self._current_worker and self._current_worker.isRunning():
            logger.info("Cancelling email refresh...")
            self._current_worker.stop()
            self._current_worker.wait(timeout=5000)  # Wait up to 5 seconds
            
            if self._current_worker.isRunning():
                logger.warning("Worker did not stop gracefully, terminating")
                self._current_worker.terminate()
                self._current_worker.wait(timeout=2000)
        
        self._cleanup_worker()
    
    def _on_emails_fetched(self, emails: List[EmailItem]):
        """Handle successful email fetch."""
        self.emails_updated.emit(emails)
    
    def _on_error(self, error_message: str):
        """Handle error during fetch."""
        self.refresh_completed.emit(False, error_message)
    
    def _on_finished(self):
        """Handle worker completion."""
        success = self._current_worker and not self._current_worker.property("error_occurred")
        
        if success and hasattr(self._current_worker, '_emails_emitted'):
            self.refresh_completed.emit(True, "Refresh completed successfully")
        elif success:
            self.refresh_completed.emit(True, "No emails to display")
        # Error case is handled by _on_error
        
        self._cleanup_worker()
    
    def _cleanup_worker(self):
        """Clean up worker resources."""
        if self._current_worker:
            self._current_worker.deleteLater()
            self._current_worker = None
        self._is_refreshing = False


class ConnectionTestController(QObject):
    """
    Controller for IMAP connection testing.
    
    Provides a simple interface for testing connections in the background.
    """
    
    # Signals
    test_started = Signal()
    test_completed = Signal(bool, str)  # (success, message)
    
    def __init__(self, parent=None):
        """Initialize the connection test controller."""
        super().__init__(parent)
        self._current_worker: Optional[ConnectionTestWorker] = None
        self._is_testing = False
    
    def is_testing(self) -> bool:
        """Check if connection test is in progress."""
        return self._is_testing
    
    def test_connection(self, config: ImapConfig):
        """
        Test IMAP connection.
        
        Args:
            config: IMAP configuration to test
        """
        if self._is_testing:
            logger.warning("Connection test already in progress, ignoring request")
            return
        
        if not config.is_complete():
            self.test_completed.emit(False, "IMAP configuration is incomplete")
            return
        
        self._is_testing = True
        self.test_started.emit()
        
        # Create and configure worker
        self._current_worker = ConnectionTestWorker(config)
        
        # Connect signals
        self._current_worker.test_completed.connect(self._on_test_completed)
        self._current_worker.finished.connect(self._on_finished)
        
        # Start worker
        self._current_worker.start()
    
    def cancel_test(self):
        """Cancel current connection test."""
        if self._current_worker and self._current_worker.isRunning():
            logger.info("Cancelling connection test...")
            self._current_worker.stop()
            self._current_worker.wait(timeout=3000)  # Wait up to 3 seconds
            
            if self._current_worker.isRunning():
                logger.warning("Test worker did not stop gracefully, terminating")
                self._current_worker.terminate()
                self._current_worker.wait(timeout=1000)
        
        self._cleanup_worker()
    
    def _on_test_completed(self, success: bool, message: str):
        """Handle connection test completion."""
        self.test_completed.emit(success, message)
    
    def _on_finished(self):
        """Handle worker completion."""
        self._cleanup_worker()
    
    def _cleanup_worker(self):
        """Clean up worker resources."""
        if self._current_worker:
            self._current_worker.deleteLater()
            self._current_worker = None
        self._is_testing = False


# Global thread pool for summary generation
_summary_thread_pool: Optional[QThreadPool] = None


def get_summary_thread_pool() -> QThreadPool:
    """
    Get the global thread pool for summary generation.
    
    Returns:
        QThreadPool instance
    """
    global _summary_thread_pool
    if _summary_thread_pool is None:
        _summary_thread_pool = QThreadPool()
        # Limit concurrent summary threads to avoid overloading
        _summary_thread_pool.setMaxThreadCount(min(4, QThreadPool.globalInstance().maxThreadCount()))
    return _summary_thread_pool


def generate_summaries_parallel(emails: List[EmailItem], max_sentences: int = 3) -> List[SummaryGenerationWorker]:
    """
    Generate summaries for multiple emails in parallel.
    
    Args:
        emails: List of EmailItem objects
        max_sentences: Maximum sentences per summary
        
    Returns:
        List of SummaryGenerationWorker instances (for connecting signals)
    """
    thread_pool = get_summary_thread_pool()
    workers = []
    
    for i, email in enumerate(emails):
        if not email.summary:  # Only generate if not already present
            worker = SummaryGenerationWorker(i, email.body_text, max_sentences)
            workers.append(worker)
            thread_pool.start(worker)
    
    return workers