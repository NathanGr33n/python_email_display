"""
Unit tests for utils.py functions.
"""
from pathlib import Path

from utils import (
    decode_email_header,
    extract_email_address,
    html_to_text,
    clean_text_for_summary,
    extract_text_snippet,
    sanitize_filename,
    format_bytes,
)


def test_decode_email_header_plain_text():
    assert decode_email_header("Hello World") == "Hello World"


def test_decode_email_header_encoded_utf8():
    encoded = "=?UTF-8?B?5pel5pys6Kqe?="  # "日本語" in Base64
    result = decode_email_header(encoded)
    assert isinstance(result, str)
    assert result != ""  # decoded non-empty


def test_extract_email_address_with_name():
    name, email = extract_email_address('John Doe <john@example.com>')
    assert name == 'John Doe'
    assert email == 'john@example.com'


def test_extract_email_address_without_name():
    name, email = extract_email_address('jane@example.com')
    assert name == ''
    assert email == 'jane@example.com'


def test_html_to_text_basic(html_email_content):
    text = html_to_text(html_email_content)
    assert 'Welcome Email' in text
    assert 'First item' in text
    assert 'Second item' in text
    assert 'alert(' not in text  # scripts removed


def test_clean_text_for_summary_removes_urls_and_emails():
    text = "Visit https://example.com or www.example.com. Email me at user@example.com"
    cleaned = clean_text_for_summary(text)
    assert '[URL]' in cleaned
    assert '[EMAIL]' in cleaned


def test_extract_text_snippet_short_text():
    text = "Short text."
    assert extract_text_snippet(text, max_chars=50) == text


def test_extract_text_snippet_long_text():
    text = "This is a long text that should be truncated properly at a sentence boundary. Another sentence follows."
    snippet = extract_text_snippet(text, max_chars=60)
    assert len(snippet) <= 63  # allow for ellipsis


def test_sanitize_filename_removes_illegal_chars():
    assert sanitize_filename('inva<>lid:na/me\\?.txt') == 'inva__lid_na_me__.txt'


def test_format_bytes_values():
    assert format_bytes(0) == '0 B'
    assert format_bytes(1023).endswith('B')
    assert format_bytes(1024).endswith('KB')
    assert format_bytes(1024*1024).endswith('MB')
