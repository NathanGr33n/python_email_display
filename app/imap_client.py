"""
IMAP client for secure email fetching and parsing.
"""
import imaplib
import email
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Optional, Tuple
from email.utils import parsedate_to_datetime

from models import EmailItem, ImapConfig
from utils import decode_email_header, extract_email_address, html_to_text, clean_text_for_summary


logger = logging.getLogger(__name__)


class ImapClientError(Exception):
    """Base exception for IMAP client errors."""
    pass


class AuthenticationError(ImapClientError):
    """Raised when IMAP authentication fails."""
    pass


class ConnectionError(ImapClientError):
    """Raised when IMAP connection fails."""
    pass


class ImapClient:
    """
    IMAP client for secure email operations.
    """
    
    def __init__(self, config: ImapConfig, timeout: int = 30):
        """
        Initialize IMAP client with configuration.
        
        Args:
            config: IMAP configuration
            timeout: Connection timeout in seconds
        """
        self.config = config
        self.timeout = timeout
        self._connection: Optional[imaplib.IMAP4_SSL] = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def connect(self) -> None:
        """
        Establish secure IMAP connection.
        
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        try:
            # Create SSL context with secure settings
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            logger.info(f"Connecting to {self.config.host}:{self.config.port}")
            
            # Connect to IMAP server
            if self.config.use_ssl:
                self._connection = imaplib.IMAP4_SSL(
                    self.config.host, 
                    self.config.port,
                    ssl_context=context
                )
            else:
                # For testing with non-SSL servers (not recommended for production)
                self._connection = imaplib.IMAP4(self.config.host, self.config.port)
                self._connection.starttls(ssl_context=context)
            
            # Set timeout
            if hasattr(self._connection, 'sock') and self._connection.sock:
                self._connection.sock.settimeout(self.timeout)
            
            # Authenticate
            logger.info(f"Authenticating as {self.config.username}")
            result = self._connection.login(self.config.username, self.config.password)
            
            if result[0] != 'OK':
                raise AuthenticationError(f"Authentication failed: {result[1]}")
            
            logger.info("IMAP connection established successfully")
            
        except imaplib.IMAP4.error as e:
            raise ConnectionError(f"IMAP connection failed: {e}")
        except ssl.SSLError as e:
            raise ConnectionError(f"SSL connection failed: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected connection error: {e}")
    
    def disconnect(self) -> None:
        """Close IMAP connection safely."""
        if self._connection:
            try:
                self._connection.close()
                self._connection.logout()
                logger.info("IMAP connection closed")
            except Exception as e:
                logger.warning(f"Error closing IMAP connection: {e}")
            finally:
                self._connection = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test IMAP connection and authentication.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            self.connect()
            
            # Try to select folder to verify full access
            result = self._connection.select(self.config.folder, readonly=True)
            if result[0] != 'OK':
                return False, f"Cannot access folder '{self.config.folder}': {result[1]}"
            
            return True, "Connection successful"
            
        except AuthenticationError as e:
            return False, f"Authentication failed: {str(e)}"
        except ConnectionError as e:
            return False, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
        finally:
            self.disconnect()
    
    def fetch_latest_emails(self, count: int = 10) -> List[EmailItem]:
        """
        Fetch the latest emails from the configured folder.
        
        Args:
            count: Number of emails to fetch
            
        Returns:
            List of EmailItem objects, sorted by date (newest first)
            
        Raises:
            ImapClientError: If fetching fails
        """
        if not self._connection:
            raise ImapClientError("Not connected to IMAP server")
        
        try:
            # Select folder
            result = self._connection.select(self.config.folder, readonly=True)
            if result[0] != 'OK':
                raise ImapClientError(f"Cannot select folder '{self.config.folder}': {result[1]}")
            
            # Search for all messages
            result = self._connection.search(None, 'ALL')
            if result[0] != 'OK':
                raise ImapClientError(f"Search failed: {result[1]}")
            
            message_ids = result[1][0].split()
            if not message_ids:
                logger.info("No messages found in folder")
                return []
            
            # Get the latest messages (IMAP message IDs are sequential)
            latest_ids = message_ids[-count:] if len(message_ids) >= count else message_ids
            latest_ids.reverse()  # Newest first
            
            emails = []
            for msg_id in latest_ids:
                try:
                    email_item = self._fetch_single_email(msg_id.decode())
                    if email_item:
                        emails.append(email_item)
                except Exception as e:
                    logger.warning(f"Failed to fetch email {msg_id}: {e}")
                    continue
            
            # Sort by date (newest first) as a safety measure
            emails.sort(key=lambda x: x.received_date, reverse=True)
            
            logger.info(f"Successfully fetched {len(emails)} emails")
            return emails
            
        except Exception as e:
            if isinstance(e, ImapClientError):
                raise
            raise ImapClientError(f"Failed to fetch emails: {e}")
    
    def _fetch_single_email(self, message_id: str) -> Optional[EmailItem]:
        """
        Fetch and parse a single email message.
        
        Args:
            message_id: IMAP message ID
            
        Returns:
            EmailItem object or None if parsing fails
        """
        try:
            # Fetch message
            result = self._connection.fetch(message_id, '(RFC822)')
            if result[0] != 'OK':
                logger.warning(f"Failed to fetch message {message_id}: {result[1]}")
                return None
            
            # Parse email message
            raw_email = result[1][0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract metadata
            sender_name, sender_email = self._extract_sender(email_message)
            subject = self._extract_subject(email_message)
            received_date = self._extract_date(email_message)
            message_uid = email_message.get('Message-ID', message_id)
            
            # Extract body text
            body_text = self._extract_body_text(email_message)
            if not body_text:
                body_text = "No readable content found."
            
            # Check for attachments
            has_attachments = self._has_attachments(email_message)
            
            return EmailItem(
                sender_name=sender_name,
                sender_email=sender_email,
                subject=subject,
                received_date=received_date,
                body_text=body_text,
                summary="",  # Will be filled by summarizer
                message_id=message_uid,
                has_attachments=has_attachments
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse message {message_id}: {e}")
            return None
    
    def _extract_sender(self, email_message: email.message.EmailMessage) -> Tuple[str, str]:
        """Extract sender name and email address."""
        from_header = email_message.get('From', '')
        if from_header:
            return extract_email_address(decode_email_header(from_header))
        return "", "unknown@unknown.com"
    
    def _extract_subject(self, email_message: email.message.EmailMessage) -> str:
        """Extract and decode email subject."""
        subject = email_message.get('Subject', '(No Subject)')
        return decode_email_header(subject)
    
    def _extract_date(self, email_message: email.message.EmailMessage) -> datetime:
        """Extract email date."""
        date_header = email_message.get('Date')
        if date_header:
            try:
                return parsedate_to_datetime(date_header)
            except Exception as e:
                logger.warning(f"Failed to parse date '{date_header}': {e}")
        
        # Fallback to current time
        return datetime.now()
    
    def _extract_body_text(self, email_message: email.message.EmailMessage) -> str:
        """
        Extract plain text content from email body.
        
        Handles both plain text and HTML content, as well as multipart messages.
        """
        body_text = ""
        
        try:
            if email_message.is_multipart():
                # Handle multipart messages
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))
                    
                    # Skip attachments
                    if 'attachment' in content_disposition:
                        continue
                    
                    if content_type == 'text/plain':
                        # Plain text part
                        text_content = self._decode_part_content(part)
                        if text_content:
                            body_text = text_content
                            break  # Prefer plain text over HTML
                    
                    elif content_type == 'text/html' and not body_text:
                        # HTML part (use only if no plain text found)
                        html_content = self._decode_part_content(part)
                        if html_content:
                            body_text = html_to_text(html_content)
            else:
                # Single part message
                content_type = email_message.get_content_type()
                if content_type == 'text/plain':
                    body_text = self._decode_part_content(email_message)
                elif content_type == 'text/html':
                    html_content = self._decode_part_content(email_message)
                    if html_content:
                        body_text = html_to_text(html_content)
        
        except Exception as e:
            logger.warning(f"Failed to extract body text: {e}")
            return "Error extracting email content."
        
        return clean_text_for_summary(body_text) if body_text else ""
    
    def _decode_part_content(self, part: email.message.EmailMessage) -> str:
        """
        Decode content from email part, handling various encodings.
        """
        try:
            # Get raw content
            content = part.get_payload(decode=True)
            if content is None:
                return ""
            
            # Determine encoding
            charset = part.get_content_charset()
            if charset is None:
                charset = 'utf-8'  # Default encoding
            
            # Decode content
            if isinstance(content, bytes):
                # Try the specified charset first
                try:
                    return content.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    # Fall back to common encodings
                    for fallback_charset in ['utf-8', 'iso-8859-1', 'windows-1252']:
                        try:
                            return content.decode(fallback_charset)
                        except UnicodeDecodeError:
                            continue
                    # Last resort: decode with error replacement
                    return content.decode('utf-8', errors='replace')
            else:
                return str(content)
                
        except Exception as e:
            logger.warning(f"Failed to decode part content: {e}")
            return ""
    
    def _has_attachments(self, email_message: email.message.EmailMessage) -> bool:
        """Check if email has attachments."""
        if not email_message.is_multipart():
            return False
        
        for part in email_message.walk():
            content_disposition = str(part.get('Content-Disposition', ''))
            if 'attachment' in content_disposition:
                return True
        
        return False
    
    def get_folder_list(self) -> List[str]:
        """
        Get list of available IMAP folders.
        
        Returns:
            List of folder names
        """
        if not self._connection:
            raise ImapClientError("Not connected to IMAP server")
        
        try:
            result = self._connection.list()
            if result[0] != 'OK':
                raise ImapClientError(f"Failed to list folders: {result[1]}")
            
            folders = []
            for folder_info in result[1]:
                if folder_info:
                    # Parse folder name from response (format: '(\\Flags) "delimiter" "name"')
                    folder_line = folder_info.decode('utf-8')
                    # Extract folder name (usually the last quoted string)
                    parts = folder_line.split('"')
                    if len(parts) >= 3:
                        folder_name = parts[-2]  # Second to last quoted part
                        folders.append(folder_name)
            
            return folders
            
        except Exception as e:
            logger.warning(f"Failed to get folder list: {e}")
            return ['INBOX']  # Fallback to default