"""
Unit tests for multiple account support.
"""
import pytest

from models import ImapConfig, AppSettings


def test_app_settings_add_account():
    settings = AppSettings()
    account1 = ImapConfig(host="imap.gmail.com", username="user1@gmail.com", password="pass1")
    account2 = ImapConfig(host="imap.outlook.com", username="user2@outlook.com", password="pass2")
    
    settings.add_account(account1)
    settings.add_account(account2)
    
    assert len(settings.imap_accounts) == 2
    assert settings.imap_accounts[0] == account1
    assert settings.imap_accounts[1] == account2


def test_app_settings_active_account():
    settings = AppSettings()
    account1 = ImapConfig(host="imap.gmail.com", username="user1@gmail.com", password="pass1")
    account2 = ImapConfig(host="imap.outlook.com", username="user2@outlook.com", password="pass2")
    
    settings.add_account(account1)
    settings.add_account(account2)
    
    assert settings.active_account == account1
    assert settings.active_account_index == 0


def test_app_settings_set_active_account():
    settings = AppSettings()
    account1 = ImapConfig(host="imap.gmail.com", username="user1@gmail.com", password="pass1")
    account2 = ImapConfig(host="imap.outlook.com", username="user2@outlook.com", password="pass2")
    
    settings.add_account(account1)
    settings.add_account(account2)
    
    settings.set_active_account(1)
    assert settings.active_account == account2
    assert settings.active_account_index == 1


def test_app_settings_remove_account():
    settings = AppSettings()
    account1 = ImapConfig(host="imap.gmail.com", username="user1@gmail.com", password="pass1")
    account2 = ImapConfig(host="imap.outlook.com", username="user2@outlook.com", password="pass2")
    
    settings.add_account(account1)
    settings.add_account(account2)
    
    settings.remove_account(0)
    assert len(settings.imap_accounts) == 1
    assert settings.imap_accounts[0] == account2


def test_app_settings_remove_active_account():
    settings = AppSettings()
    account1 = ImapConfig(host="imap.gmail.com", username="user1@gmail.com", password="pass1")
    account2 = ImapConfig(host="imap.outlook.com", username="user2@outlook.com", password="pass2")
    
    settings.add_account(account1)
    settings.add_account(account2)
    settings.set_active_account(1)
    
    settings.remove_account(1)
    assert len(settings.imap_accounts) == 1
    assert settings.active_account_index == 0
    assert settings.active_account == account1


def test_app_settings_no_accounts():
    settings = AppSettings()
    assert settings.active_account is None
    assert settings.imap is None  # Legacy property


def test_imap_config_get_display_name_with_name():
    config = ImapConfig(
        host="imap.gmail.com",
        username="user@gmail.com",
        password="pass",
        account_name="Work Email"
    )
    assert config.get_display_name() == "Work Email"


def test_imap_config_get_display_name_without_name():
    config = ImapConfig(
        host="imap.gmail.com",
        username="user@gmail.com",
        password="pass"
    )
    assert config.get_display_name() == "user@gmail.com"


def test_imap_config_get_display_name_empty():
    config = ImapConfig(host="imap.gmail.com")
    assert config.get_display_name() == "Unnamed Account"
