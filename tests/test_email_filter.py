"""
Unit tests for EmailFilter and email filtering functionality.
"""
from datetime import datetime, date
import pytest

from models import EmailItem, EmailFilter


@pytest.fixture
def sample_emails():
    """Create a list of sample emails for filtering tests."""
    return [
        EmailItem(
            sender_name="Alice Smith",
            sender_email="alice@example.com",
            subject="Project Update",
            received_date=datetime(2025, 12, 1, 10, 0),
            body_text="This is a project update email with important information.",
            summary="Project update with important information.",
            has_attachments=True
        ),
        EmailItem(
            sender_name="Bob Jones",
            sender_email="bob@company.com",
            subject="Meeting Tomorrow",
            received_date=datetime(2025, 12, 3, 14, 30),
            body_text="Reminder about the meeting scheduled for tomorrow morning.",
            summary="Meeting reminder for tomorrow.",
            has_attachments=False
        ),
        EmailItem(
            sender_name="Charlie Brown",
            sender_email="charlie@test.com",
            subject="Invoice #12345",
            received_date=datetime(2025, 12, 5, 9, 15),
            body_text="Please find attached the invoice for services rendered.",
            summary="Invoice attached for services.",
            has_attachments=True
        ),
    ]


def test_email_filter_no_criteria():
    email_filter = EmailFilter()
    assert not email_filter.is_active()


def test_email_filter_with_search_query():
    email_filter = EmailFilter(search_query="test")
    assert email_filter.is_active()


def test_email_filter_clear():
    email_filter = EmailFilter(search_query="test", sender_filter="alice")
    email_filter.clear()
    assert not email_filter.is_active()
    assert email_filter.search_query == ""
    assert email_filter.sender_filter == ""


def test_email_matches_search_query(sample_emails):
    email_filter = EmailFilter(search_query="project")
    assert sample_emails[0].matches_filter(email_filter)
    assert not sample_emails[1].matches_filter(email_filter)


def test_email_matches_sender_filter(sample_emails):
    email_filter = EmailFilter(sender_filter="alice")
    assert sample_emails[0].matches_filter(email_filter)
    assert not sample_emails[1].matches_filter(email_filter)


def test_email_matches_date_from(sample_emails):
    email_filter = EmailFilter(date_from=date(2025, 12, 2))
    assert not sample_emails[0].matches_filter(email_filter)  # Dec 1
    assert sample_emails[1].matches_filter(email_filter)     # Dec 3
    assert sample_emails[2].matches_filter(email_filter)     # Dec 5


def test_email_matches_date_to(sample_emails):
    email_filter = EmailFilter(date_to=date(2025, 12, 3))
    assert sample_emails[0].matches_filter(email_filter)     # Dec 1
    assert sample_emails[1].matches_filter(email_filter)     # Dec 3
    assert not sample_emails[2].matches_filter(email_filter) # Dec 5


def test_email_matches_attachments_filter(sample_emails):
    email_filter = EmailFilter(has_attachments=True)
    assert sample_emails[0].matches_filter(email_filter)
    assert not sample_emails[1].matches_filter(email_filter)
    assert sample_emails[2].matches_filter(email_filter)


def test_email_matches_combined_filters(sample_emails):
    email_filter = EmailFilter(
        search_query="invoice",
        has_attachments=True
    )
    assert not sample_emails[0].matches_filter(email_filter)
    assert not sample_emails[1].matches_filter(email_filter)
    assert sample_emails[2].matches_filter(email_filter)


def test_email_no_match(sample_emails):
    email_filter = EmailFilter(search_query="nonexistent")
    assert not sample_emails[0].matches_filter(email_filter)
    assert not sample_emails[1].matches_filter(email_filter)
    assert not sample_emails[2].matches_filter(email_filter)
