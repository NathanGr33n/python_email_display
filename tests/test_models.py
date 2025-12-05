"""
Unit tests for models.py data classes.
"""
from datetime import datetime, timedelta
import pytest

from models import EmailItem, ImapConfig, AppSettings


def test_email_item_creation(sample_email):
    assert sample_email.sender_name == "John Doe"
    assert sample_email.sender_email == "john.doe@example.com"
    assert sample_email.subject == "Test Email Subject"


def test_email_item_sender_display_with_name():
    email = EmailItem(
        sender_name="Alice Smith",
        sender_email="alice@example.com",
        subject="Test",
        received_date=datetime.now(),
        body_text="Test body",
        summary="Test summary"
    )
    assert email.sender_display == "Alice Smith <alice@example.com>"


def test_email_item_sender_display_no_name():
    email = EmailItem(
        sender_name="",
        sender_email="bob@example.com",
        subject="Test",
        received_date=datetime.now(),
        body_text="Test body",
        summary="Test summary"
    )
    assert email.sender_display == "bob@example.com"


def test_email_item_date_display():
    email = EmailItem(
        sender_name="Test",
        sender_email="test@example.com",
        subject="Test",
        received_date=datetime(2025, 12, 5, 14, 30, 0),
        body_text="Test",
        summary="Test"
    )
    assert email.date_display == "2025-12-05 14:30"


def test_email_item_date_tooltip_just_now():
    now = datetime.now()
    email = EmailItem(
        sender_name="Test",
        sender_email="test@example.com",
        subject="Test",
        received_date=now - timedelta(seconds=30),
        body_text="Test",
        summary="Test"
    )
    tooltip = email.date_tooltip
    assert "Just now" in tooltip or "0 minutes ago" in tooltip


def test_email_item_date_tooltip_hours_ago():
    now = datetime.now()
    email = EmailItem(
        sender_name="Test",
        sender_email="test@example.com",
        subject="Test",
        received_date=now - timedelta(hours=5),
        body_text="Test",
        summary="Test"
    )
    assert "5 hours ago" in email.date_tooltip


def test_email_item_date_tooltip_yesterday():
    now = datetime.now()
    email = EmailItem(
        sender_name="Test",
        sender_email="test@example.com",
        subject="Test",
        received_date=now - timedelta(days=1),
        body_text="Test",
        summary="Test"
    )
    assert "Yesterday" in email.date_tooltip


def test_imap_config_is_complete_valid(sample_imap_config):
    assert sample_imap_config.is_complete() is True


def test_imap_config_is_complete_missing_host():
    config = ImapConfig(host="", username="test@example.com", password="pass")
    assert config.is_complete() is False


def test_imap_config_is_complete_missing_username():
    config = ImapConfig(host="imap.gmail.com", username="", password="pass")
    assert config.is_complete() is False


def test_imap_config_is_complete_missing_password():
    config = ImapConfig(host="imap.gmail.com", username="test@example.com", password="")
    assert config.is_complete() is False


def test_imap_config_default_values():
    config = ImapConfig(host="imap.example.com")
    assert config.port == 993
    assert config.use_ssl is True
    assert config.folder == "INBOX"


def test_app_settings_creation(sample_app_settings):
    assert sample_app_settings.max_emails_to_fetch == 10
    assert sample_app_settings.summary_sentences == 3
    assert sample_app_settings.auto_refresh_on_startup is True


def test_app_settings_default_values(sample_imap_config):
    settings = AppSettings()
    settings.add_account(sample_imap_config)
    assert settings.auto_refresh_on_startup is True
    assert settings.use_keyring is True
    assert settings.max_emails_to_fetch == 10
    assert settings.summary_sentences == 3
    assert settings.connection_timeout == 30
    assert len(settings.imap_accounts) == 1
    assert settings.active_account == sample_imap_config
