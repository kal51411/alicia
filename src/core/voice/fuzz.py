"""
Alicia Fuzzy Matching Utility
Provides fuzzy string comparison and wake-word matching using SequenceMatcher.
"""

from difflib import SequenceMatcher
from typing import List, Optional, Tuple


def similarity_ratio(a: str, b: str) -> float:
    """Calculate ratio between 0.0 and 1.0."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def matches_wake_word(text: str, wake_words: Optional[List[str]] = None, threshold: float = 0.75) -> Tuple[bool, str]:
    """
    Check if user speech contains or sounds like one of the wake words.
    Returns (matched: bool, detected_word: str).
    """
    if not text:
        return False, ""

    words = wake_words or ["alicia", "hey alicia", "elicia", "alisa", "aleesha", "alisha"]
    text_lower = text.lower().strip()

    # Exact substring check
    for w in words:
        if w in text_lower:
            return True, w

    # Token-level fuzzy check
    tokens = text_lower.split()
    for token in tokens:
        for w in words:
            if similarity_ratio(token, w) >= threshold:
                return True, w

    # Bigram check for multi-word wake phrases (e.g. "hey alicia")
    if len(tokens) >= 2:
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]} {tokens[i+1]}"
            for w in words:
                if similarity_ratio(bigram, w) >= threshold:
                    return True, w

    return False, ""


def find_best_match(query: str, choices: List[str], cutoff: float = 0.6) -> Optional[str]:
    """Find the closest matching string from a list of choices."""
    best_score = 0.0
    best_match = None
    for choice in choices:
        score = similarity_ratio(query, choice)
        if score > best_score and score >= cutoff:
            best_score = score
            best_match = choice
    return best_match
