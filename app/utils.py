"""
Utility functions for the Email Summarizer application.
"""
import re
import html
import logging
from email.header import decode_header
from typing import Optional, Tuple
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


def decode_email_header(header: str) -> str:
    """
    Decode email headers that might be encoded (e.g., =?UTF-8?B?...?=).
    
    Args:
        header: Raw email header string
        
    Returns:
        Decoded header string
    """
    try:
        decoded_parts = decode_header(header)
        result = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    result += part.decode(encoding)
                else:
                    # Try common encodings
                    for enc in ['utf-8', 'iso-8859-1', 'windows-1252']:
                        try:
                            result += part.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # If all fail, use errors='replace'
                        result += part.decode('utf-8', errors='replace')
            else:
                result += str(part)
                
        return result.strip()
    except Exception as e:
        logger.warning(f"Failed to decode header '{header}': {e}")
        return str(header)


def extract_email_address(addr_string: str) -> Tuple[str, str]:
    """
    Extract name and email from address string.
    
    Args:
        addr_string: Email address string like "Name <email@domain.com>" or just "email@domain.com"
        
    Returns:
        Tuple of (name, email_address)
    """
    addr_string = addr_string.strip()
    
    # Pattern for "Name <email@domain.com>"
    match = re.match(r'^(.+?)\s*<([^>]+)>$', addr_string)
    if match:
        name = decode_email_header(match.group(1).strip().strip('"\''))
        email = match.group(2).strip()
        return name, email
    
    # Just an email address
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', addr_string)
    if email_match:
        email = email_match.group()
        return "", email
    
    # Fallback
    return "", addr_string


def html_to_text(html_content: str) -> str:
    """
    Convert HTML content to clean plain text.
    
    Args:
        html_content: HTML string
        
    Returns:
        Plain text string with formatting preserved where possible
    """
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'meta', 'link']):
            element.decompose()
        
        # Add line breaks for block elements
        for element in soup.find_all(['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            element.insert_after('\n')
        
        # Add extra breaks for list items
        for element in soup.find_all(['li']):
            element.insert_before('• ')
            element.insert_after('\n')
            
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]  # Remove empty lines
        
        return '\n'.join(lines)
        
    except Exception as e:
        logger.warning(f"Failed to parse HTML content: {e}")
        # Fallback: strip HTML tags manually
        text = re.sub(r'<[^>]+>', '', html_content)
        return html.unescape(text).strip()


def clean_text_for_summary(text: str, max_length: int = 10000) -> str:
    """
    Clean and prepare text for summarization.
    
    Args:
        text: Raw text content
        max_length: Maximum length to truncate to
        
    Returns:
        Cleaned text ready for summarization
    """
    if not text:
        return ""
    
    # Unescape HTML entities
    text = html.unescape(text)
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Multiple newlines to double
    text = re.sub(r'[ \t]+', ' ', text)       # Multiple spaces/tabs to single
    
    # Remove common email artifacts
    text = re.sub(r'--+', '', text)          # Signature separators
    text = re.sub(r'_{3,}', '', text)        # Underline separators
    text = re.sub(r'={3,}', '', text)        # Equal sign separators
    
    # Remove URLs (they add noise to summaries)
    text = re.sub(r'https?://[^\s<>"]+', '[URL]', text)
    text = re.sub(r'www\.[^\s<>"]+', '[URL]', text)
    
    # Remove email addresses in body (privacy)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()


def extract_text_snippet(text: str, max_chars: int = 300) -> str:
    """
    Extract a snippet from text as fallback when summarization fails.
    
    Args:
        text: Source text
        max_chars: Maximum characters in snippet
        
    Returns:
        Text snippet ending at sentence boundary if possible
    """
    if not text:
        return "No content available."
    
    text = text.strip()
    
    if len(text) <= max_chars:
        return text
    
    # Try to cut at sentence boundary
    truncated = text[:max_chars]
    
    # Find last sentence-ending punctuation
    sentence_end = max(
        truncated.rfind('.'),
        truncated.rfind('!'),
        truncated.rfind('?')
    )
    
    if sentence_end > max_chars * 0.5:  # Only use if we don't lose too much
        return truncated[:sentence_end + 1].strip()
    
    # Fallback: cut at word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.8:
        return truncated[:last_space].strip() + "..."
    
    return truncated.strip() + "..."


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove/replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f]', '', filename)  # Control characters
    filename = filename.strip('. ')  # Leading/trailing dots and spaces
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename or "untitled"


def format_bytes(size_bytes: int) -> str:
    """
    Format byte size in human readable form.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string (e.g., "1.2 MB")
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    size_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and size_index < len(size_names) - 1:
        size /= 1024.0
        size_index += 1
    
    return f"{size:.1f} {size_names[size_index]}"