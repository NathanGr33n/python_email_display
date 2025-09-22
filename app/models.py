"""
Data models for the Email Summarizer application.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class EmailItem:
    """Represents a single email with all necessary display information."""
    
    # Email metadata
    sender_name: str
    sender_email: str
    subject: str
    received_date: datetime
    
    # Content
    body_text: str  # Plain text content extracted from email
    summary: str    # Generated summary (2-3 sentences)
    
    # Optional fields
    message_id: Optional[str] = None
    has_attachments: bool = False
    
    @property
    def sender_display(self) -> str:
        """Format sender for display: 'Name <email>' or just 'email' if no name."""
        if self.sender_name and self.sender_name != self.sender_email:
            return f"{self.sender_name} <{self.sender_email}>"
        return self.sender_email
    
    @property
    def date_display(self) -> str:
        """Format date for display (absolute format)."""
        return self.received_date.strftime("%Y-%m-%d %H:%M")
    
    @property
    def date_tooltip(self) -> str:
        """Relative date for tooltip display."""
        now = datetime.now()
        diff = now - self.received_date
        
        if diff.days == 0:
            if diff.seconds < 3600:  # Less than 1 hour
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago" if minutes > 1 else "Just now"
            else:  # Less than 24 hours
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.days == 1:
            return "Yesterday"
        elif diff.days < 7:
            return f"{diff.days} days ago"
        elif diff.days < 30:
            weeks = diff.days // 7
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        elif diff.days < 365:
            months = diff.days // 30
            return f"{months} month{'s' if months != 1 else ''} ago"
        else:
            years = diff.days // 365
            return f"{years} year{'s' if years != 1 else ''} ago"


@dataclass
class ImapConfig:
    """Configuration for IMAP connection."""
    
    host: str
    port: int = 993
    username: str = ""
    password: str = ""
    use_ssl: bool = True
    folder: str = "INBOX"
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        return bool(self.host and self.username and self.password)


@dataclass 
class AppSettings:
    """Application settings and preferences."""
    
    # IMAP configuration
    imap: ImapConfig
    
    # UI preferences
    auto_refresh_on_startup: bool = True
    use_keyring: bool = True  # Prefer keyring over .env
    
    # Advanced settings
    max_emails_to_fetch: int = 10
    summary_sentences: int = 3
    connection_timeout: int = 30  # seconds