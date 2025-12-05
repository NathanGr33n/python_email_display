"""
Pytest configuration and shared fixtures for Email Summarizer tests.
"""
import sys
from pathlib import Path
from datetime import datetime
import pytest

# Add app directory to path for imports
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from models import EmailItem, ImapConfig, AppSettings


@pytest.fixture
def sample_email():
    """Sample EmailItem for testing."""
    return EmailItem(
        sender_name="John Doe",
        sender_email="john.doe@example.com",
        subject="Test Email Subject",
        received_date=datetime(2025, 12, 5, 10, 30, 0),
        body_text="This is a test email body with some content. It has multiple sentences for testing purposes.",
        summary="This is a test email body with some content.",
        message_id="<test123@example.com>",
        has_attachments=False
    )


@pytest.fixture
def sample_imap_config():
    """Sample ImapConfig for testing."""
    return ImapConfig(
        host="imap.gmail.com",
        port=993,
        username="test@gmail.com",
        password="test_password",
        use_ssl=True,
        folder="INBOX"
    )


@pytest.fixture
def sample_app_settings(sample_imap_config):
    """Sample AppSettings for testing."""
    settings = AppSettings(
        auto_refresh_on_startup=True,
        use_keyring=True,
        max_emails_to_fetch=10,
        summary_sentences=3,
        connection_timeout=30
    )
    settings.add_account(sample_imap_config)
    return settings


@pytest.fixture
def html_email_content():
    """Sample HTML email content for testing."""
    return """
    <html>
        <head><style>body { color: black; }</style></head>
        <body>
            <h1>Welcome Email</h1>
            <p>This is the first paragraph with some information.</p>
            <p>This is the second paragraph with more details.</p>
            <ul>
                <li>First item</li>
                <li>Second item</li>
            </ul>
            <script>alert('test');</script>
        </body>
    </html>
    """


@pytest.fixture
def long_text_for_summary():
    """Long text suitable for summarization testing."""
    return """
    Artificial intelligence has made significant strides in recent years. Machine learning algorithms 
    are now capable of performing complex tasks that were once thought to require human intelligence. 
    Deep learning, a subset of machine learning, has been particularly successful in areas like image 
    recognition and natural language processing. Neural networks, the foundation of deep learning, 
    are inspired by the structure of the human brain. These networks consist of layers of interconnected 
    nodes that process information. The training process involves feeding large amounts of data to the 
    network and adjusting the connections based on the output. This allows the network to learn patterns 
    and make predictions. However, there are still challenges to overcome, including the need for large 
    amounts of training data and the difficulty of explaining how neural networks make decisions.
    """
