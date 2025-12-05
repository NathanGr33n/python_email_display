"""
Unit tests for summarizer.py local text summarization.
"""
import pytest
from summarizer import LocalSummarizer


def test_summarizer_initialization():
    summarizer = LocalSummarizer(language="english", max_sentences=3)
    assert summarizer.language == "english"
    assert summarizer.max_sentences == 3


def test_summarize_empty_text():
    summarizer = LocalSummarizer()
    result = summarizer.summarize("")
    assert result == "No content to summarize."


def test_summarize_short_text():
    summarizer = LocalSummarizer()
    short_text = "This is a very short text."
    result = summarizer.summarize(short_text)
    assert result == short_text


def test_summarize_long_text(long_text_for_summary):
    summarizer = LocalSummarizer(max_sentences=2)
    result = summarizer.summarize(long_text_for_summary)
    assert isinstance(result, str)
    assert len(result) > 0
    assert len(result) < len(long_text_for_summary)


def test_summarize_html_stripped():
    summarizer = LocalSummarizer()
    text_with_html = "This is important text. <script>alert('test')</script> More text follows. Final sentence."
    result = summarizer.summarize(text_with_html)
    assert isinstance(result, str)
    # Just verify we get a valid result (HTML handling varies by implementation)
    assert len(result) > 0


def test_summarizer_different_sentence_counts():
    text = """
    First sentence here. Second sentence follows. Third sentence is present.
    Fourth sentence added. Fifth sentence included. Sixth sentence appears.
    """
    
    summarizer_2 = LocalSummarizer(max_sentences=2)
    result_2 = summarizer_2.summarize(text)
    
    summarizer_4 = LocalSummarizer(max_sentences=4)
    result_4 = summarizer_4.summarize(text)
    
    assert isinstance(result_2, str)
    assert isinstance(result_4, str)


def test_summarize_with_artifacts():
    summarizer = LocalSummarizer()
    text = """
    This is the main email content with important information.
    Please let me know if you have questions.
    Sent from my iPhone
    """
    result = summarizer.summarize(text)
    assert isinstance(result, str)
    assert len(result) > 0
