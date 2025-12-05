"""
Data models for the Email Summarizer application.
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List


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
    
    def matches_filter(self, filter_criteria: 'EmailFilter') -> bool:
        """Check if email matches the given filter criteria."""
        # Search query check
        if filter_criteria.search_query:
            query_lower = filter_criteria.search_query.lower()
            if not any([
                query_lower in self.subject.lower(),
                query_lower in self.sender_name.lower(),
                query_lower in self.sender_email.lower(),
                query_lower in self.body_text.lower(),
                query_lower in self.summary.lower()
            ]):
                return False
        
        # Sender filter
        if filter_criteria.sender_filter:
            sender_lower = filter_criteria.sender_filter.lower()
            if not (sender_lower in self.sender_name.lower() or 
                   sender_lower in self.sender_email.lower()):
                return False
        
        # Date range filter
        if filter_criteria.date_from:
            if self.received_date.date() < filter_criteria.date_from:
                return False
        
        if filter_criteria.date_to:
            if self.received_date.date() > filter_criteria.date_to:
                return False
        
        # Attachments filter
        if filter_criteria.has_attachments is not None:
            if self.has_attachments != filter_criteria.has_attachments:
                return False
        
        return True


@dataclass
class EmailFilter:
    """Filter criteria for searching and filtering emails."""
    search_query: str = ""
    sender_filter: str = ""
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    has_attachments: Optional[bool] = None
    
    def is_active(self) -> bool:
        """Check if any filter is applied."""
        return bool(
            self.search_query or 
            self.sender_filter or 
            self.date_from or 
            self.date_to or 
            self.has_attachments is not None
        )
    
    def clear(self):
        """Reset all filter criteria."""
        self.search_query = ""
        self.sender_filter = ""
        self.date_from = None
        self.date_to = None
        self.has_attachments = None


@dataclass
class ImapConfig:
    """Configuration for IMAP connection."""
    
    host: str
    port: int = 993
    username: str = ""
    password: str = ""
    use_ssl: bool = True
    folder: str = "INBOX"
    account_name: str = ""  # Friendly name for the account
    
    def is_complete(self) -> bool:
        """Check if all required fields are filled."""
        return bool(self.host and self.username and self.password)
    
    def get_display_name(self) -> str:
        """Get display name for account."""
        if self.account_name:
            return self.account_name
        if self.username:
            return self.username
        return "Unnamed Account"


@dataclass 
class AppSettings:
    """Application settings and preferences."""
    
    # IMAP configurations (multiple accounts support)
    imap_accounts: List[ImapConfig] = field(default_factory=list)
    active_account_index: int = 0
    
    # UI preferences
    auto_refresh_on_startup: bool = True
    use_keyring: bool = True  # Prefer keyring over .env
    enable_notifications: bool = False
    notification_check_interval: int = 300  # seconds (5 minutes)
    
    # Advanced settings
    max_emails_to_fetch: int = 10
    summary_sentences: int = 3
    connection_timeout: int = 30  # seconds
    
    @property
    def active_account(self) -> Optional[ImapConfig]:
        """Get the currently active IMAP account."""
        if 0 <= self.active_account_index < len(self.imap_accounts):
            return self.imap_accounts[self.active_account_index]
        return None
    
    def add_account(self, account: ImapConfig):
        """Add a new IMAP account."""
        self.imap_accounts.append(account)
    
    def remove_account(self, index: int):
        """Remove an IMAP account by index."""
        if 0 <= index < len(self.imap_accounts):
            del self.imap_accounts[index]
            # Adjust active index if needed
            if self.active_account_index >= len(self.imap_accounts):
                self.active_account_index = max(0, len(self.imap_accounts) - 1)
    
    def set_active_account(self, index: int):
        """Set the active account by index."""
        if 0 <= index < len(self.imap_accounts):
            self.active_account_index = index
    
    # Legacy support for single account
    @property
    def imap(self) -> Optional[ImapConfig]:
        """Legacy property for backward compatibility."""
        return self.active_account
