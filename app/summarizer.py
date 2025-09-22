"""
Local text summarization using TextRank algorithm with fallback extraction.
"""
import logging
import re
from typing import List, Optional
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

from utils import extract_text_snippet


logger = logging.getLogger(__name__)


class SummarizerError(Exception):
    """Exception raised when summarization fails."""
    pass


class LocalSummarizer:
    """
    Local text summarizer using TextRank algorithm.
    
    Provides fallback to extractive snippets when TextRank fails.
    """
    
    def __init__(self, language: str = "english", max_sentences: int = 3):
        """
        Initialize the summarizer.
        
        Args:
            language: Language for stop words and stemming
            max_sentences: Maximum number of sentences in summary
        """
        self.language = language
        self.max_sentences = max_sentences
        
        try:
            self.stemmer = Stemmer(language)
            self.stop_words = get_stop_words(language)
            self.tokenizer = Tokenizer(language)
            self.summarizer = TextRankSummarizer(self.stemmer)
            self.summarizer.stop_words = self.stop_words
            logger.debug(f"Initialized TextRank summarizer for {language}")
        except Exception as e:
            logger.warning(f"Failed to initialize TextRank components: {e}")
            self.stemmer = None
            self.tokenizer = None
            self.summarizer = None
    
    def summarize(self, text: str) -> str:
        """
        Generate a summary of the input text.
        
        Args:
            text: Input text to summarize
            
        Returns:
            Summary text (2-3 sentences)
        """
        if not text or not text.strip():
            return "No content to summarize."
        
        text = text.strip()
        
        # Quick check for very short texts
        if len(text) < 100:
            return self._clean_short_text(text)
        
        # Try TextRank summarization first
        if self.summarizer is not None:
            try:
                summary = self._textrank_summarize(text)
                if summary:
                    return summary
            except Exception as e:
                logger.warning(f"TextRank summarization failed: {e}")
        
        # Fallback to extractive summary
        logger.debug("Using fallback extractive summary")
        return self._extractive_summarize(text)
    
    def _textrank_summarize(self, text: str) -> Optional[str]:
        """
        Perform TextRank summarization.
        
        Args:
            text: Input text
            
        Returns:
            TextRank summary or None if failed
        """
        try:
            # Parse text
            parser = PlaintextParser.from_string(text, self.tokenizer)
            document = parser.document
            
            # Check if we have enough sentences
            sentences = list(document.sentences)
            if len(sentences) < 2:
                return self._clean_short_text(text)
            
            # If text is short, return cleaned version
            if len(sentences) <= self.max_sentences:
                return self._join_sentences(sentences[:self.max_sentences])
            
            # Generate summary
            summary_sentences = self.summarizer(document, self.max_sentences)
            
            if not summary_sentences:
                return None
            
            # Convert to strings and clean
            summary_text = " ".join(str(sentence) for sentence in summary_sentences)
            return self._clean_summary_text(summary_text)
            
        except Exception as e:
            logger.debug(f"TextRank failed: {e}")
            return None
    
    def _extractive_summarize(self, text: str) -> str:
        """
        Create an extractive summary using sentence ranking.
        
        Args:
            text: Input text
            
        Returns:
            Extractive summary
        """
        try:
            # Split into sentences
            sentences = self._split_sentences(text)
            if not sentences:
                return extract_text_snippet(text, 300)
            
            if len(sentences) <= self.max_sentences:
                return " ".join(sentences[:self.max_sentences])
            
            # Score sentences by various factors
            scored_sentences = self._score_sentences(sentences)
            
            # Select top sentences
            top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)
            selected = top_sentences[:self.max_sentences]
            
            # Sort by original order and join
            selected.sort(key=lambda x: x[2])  # Sort by original position
            summary = " ".join(sentence for sentence, _, _ in selected)
            
            return self._clean_summary_text(summary)
            
        except Exception as e:
            logger.warning(f"Extractive summarization failed: {e}")
            return extract_text_snippet(text, 300)
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using regex.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Basic sentence splitting regex
        sentence_endings = r'[.!?]+\s+'
        sentences = re.split(sentence_endings, text)
        
        # Clean and filter sentences
        cleaned = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:  # Ignore very short fragments
                # Remove common email artifacts
                if not self._is_artifact_sentence(sentence):
                    cleaned.append(sentence)
        
        return cleaned
    
    def _is_artifact_sentence(self, sentence: str) -> bool:
        """
        Check if sentence is likely an email artifact (signature, etc.).
        
        Args:
            sentence: Sentence to check
            
        Returns:
            True if sentence appears to be an artifact
        """
        sentence_lower = sentence.lower().strip()
        
        # Common artifacts
        artifacts = [
            'sent from my',
            'this email was sent',
            'unsubscribe',
            'privacy policy',
            'terms of service',
            'confidentiality notice',
            'virus-free',
            'scanned by',
            'this message is intended',
            'please consider the environment'
        ]
        
        for artifact in artifacts:
            if artifact in sentence_lower:
                return True
        
        # Very short sentences that are likely artifacts
        if len(sentence.strip()) < 20 and any(word in sentence_lower for word in ['regards', 'thanks', 'best', 'sincerely']):
            return True
        
        return False
    
    def _score_sentences(self, sentences: List[str]) -> List[tuple]:
        """
        Score sentences for importance.
        
        Args:
            sentences: List of sentences
            
        Returns:
            List of (sentence, score, original_position) tuples
        """
        scored = []
        
        for i, sentence in enumerate(sentences):
            score = 0.0
            sentence_lower = sentence.lower()
            words = sentence_lower.split()
            
            # Length bonus (prefer medium-length sentences)
            word_count = len(words)
            if 10 <= word_count <= 30:
                score += 1.0
            elif word_count < 10:
                score += 0.3
            
            # Position bonus (first few sentences often important)
            if i < 3:
                score += 0.5 * (3 - i) / 3
            
            # Keyword importance (simple term frequency)
            important_words = ['important', 'urgent', 'notice', 'update', 'new', 'please', 'required']
            for word in important_words:
                if word in sentence_lower:
                    score += 0.3
            
            # Penalize questions (often less informative in summaries)
            if sentence.strip().endswith('?'):
                score -= 0.2
            
            # Penalize very long sentences (may be less readable)
            if word_count > 40:
                score -= 0.3
            
            scored.append((sentence, score, i))
        
        return scored
    
    def _join_sentences(self, sentences) -> str:
        """Join sentences from sumy objects."""
        return " ".join(str(sentence) for sentence in sentences)
    
    def _clean_short_text(self, text: str) -> str:
        """
        Clean and format short text for display.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Ensure it ends with proper punctuation
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        return text
    
    def _clean_summary_text(self, summary: str) -> str:
        """
        Clean and format summary text.
        
        Args:
            summary: Raw summary text
            
        Returns:
            Cleaned summary text
        """
        if not summary:
            return "Unable to generate summary."
        
        # Remove excessive whitespace
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        # Remove common artifacts
        summary = re.sub(r'\[URL\]', '', summary)
        summary = re.sub(r'\[EMAIL\]', '', summary)
        
        # Ensure proper spacing after periods
        summary = re.sub(r'\.(\w)', r'. \1', summary)
        
        # Limit length to be reasonable for display
        if len(summary) > 500:  # Too long for a summary
            summary = extract_text_snippet(summary, 450)
        
        # Ensure proper ending
        if summary and not summary.endswith(('.', '!', '?')):
            # Try to end at last complete sentence
            last_punct = max(summary.rfind('.'), summary.rfind('!'), summary.rfind('?'))
            if last_punct > len(summary) * 0.7:  # If punctuation is near the end
                summary = summary[:last_punct + 1]
            else:
                summary += '.'
        
        return summary or "Unable to generate meaningful summary."
    
    def is_available(self) -> bool:
        """
        Check if TextRank summarizer is available.
        
        Returns:
            True if TextRank is properly initialized
        """
        return self.summarizer is not None
    
    def get_info(self) -> dict:
        """
        Get information about the summarizer.
        
        Returns:
            Dictionary with summarizer info
        """
        return {
            'algorithm': 'TextRank' if self.is_available() else 'Extractive',
            'language': self.language,
            'max_sentences': self.max_sentences,
            'fallback_available': True
        }


# Global summarizer instance
_global_summarizer: Optional[LocalSummarizer] = None


def get_summarizer() -> LocalSummarizer:
    """
    Get the global summarizer instance (singleton pattern).
    
    Returns:
        LocalSummarizer instance
    """
    global _global_summarizer
    if _global_summarizer is None:
        _global_summarizer = LocalSummarizer()
    return _global_summarizer


def summarize_text(text: str, max_sentences: int = 3) -> str:
    """
    Convenience function to summarize text.
    
    Args:
        text: Text to summarize
        max_sentences: Maximum sentences in summary
        
    Returns:
        Summary text
    """
    summarizer = get_summarizer()
    summarizer.max_sentences = max_sentences
    return summarizer.summarize(text)