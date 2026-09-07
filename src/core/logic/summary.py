"""
Alicia Hugging Face & Pretrained Text Summarizer
Leverages Hugging Face models (BART, DistilBART, Pegasus), local pipelines,
and offline NLP ranking algorithms for fast text summarization.
"""

import os
import re
from typing import Optional, List

try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

from config.settings import settings
from src.core.logic.model import gemini_model


class HuggingFaceSummarizer:
    """Pretrained summarizer using Hugging Face models and offline fallbacks."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        token: Optional[str] = None
    ):
        self.model_name = model_name or settings.ai.hf_summarizer_model or "facebook/bart-large-cnn"
        self.token = token or settings.ai.hf_token
        self.hf_client = None
        self.local_pipeline = None

        self._init_client()

    def _init_client(self):
        if InferenceClient:
            try:
                self.hf_client = InferenceClient(token=self.token)
            except Exception as e:
                print(f"[Summarizer] Hugging Face client init notice: {e}")

    def summarize_huggingface(self, text: str, max_length: int = 130, min_length: int = 30) -> Optional[str]:
        """Summarize text using Hugging Face pretrained model."""
        if not self.hf_client:
            return None

        try:
            res = self.hf_client.summarization(
                text=text,
                model=self.model_name,
                generate_parameters={"max_length": max_length, "min_length": min_length}
            )
            if hasattr(res, "summary_text") and res.summary_text:
                return res.summary_text.strip()
            if isinstance(res, str) and res:
                return res.strip()
            return None
        except Exception as e:
            # Often 401 if token is missing, or network error
            return None

    def summarize_local_pipeline(self, text: str) -> Optional[str]:
        """Try local transformers pipeline if models are cached locally."""
        if pipeline is None:
            return None
        try:
            if self.local_pipeline is None:
                self.local_pipeline = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
            res = self.local_pipeline(text, max_length=100, min_length=25, do_sample=False)
            if res and isinstance(res, list) and "summary_text" in res[0]:
                return res[0]["summary_text"].strip()
            return None
        except Exception:
            return None

    def summarize_extractive(self, text: str, max_sentences: int = 2) -> str:
        """Intelligent offline extractive summarization using word-frequency scoring."""
        if not text:
            return ""

        # Normalize whitespace and split into sentences
        clean = re.sub(r"\s+", " ", text).strip()
        raw_sentences = re.split(r"(?<=[.!?])\s+", clean)
        sentences = [s.strip() for s in raw_sentences if len(s.split()) >= 4]

        if not sentences:
            return clean[:200]
        if len(sentences) <= max_sentences:
            return " ".join(sentences)

        # Word frequency map
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
            "about", "against", "between", "into", "through", "during", "before", "after",
            "above", "below", "from", "up", "down", "of", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where", "why", "how",
            "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
            "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s",
            "t", "can", "will", "just", "don", "should", "now", "is", "are", "was", "were"
        }
        words = re.findall(r"\w+", clean.lower())
        freq_table = {}
        for word in words:
            if word not in stopwords and len(word) > 2:
                freq_table[word] = freq_table.get(word, 0) + 1

        if not freq_table:
            return " ".join(sentences[:max_sentences])

        max_freq = max(freq_table.values())
        for word in freq_table:
            freq_table[word] /= max_freq

        # Score sentences
        sentence_scores = {}
        for sentence in sentences:
            score = 0
            for word in re.findall(r"\w+", sentence.lower()):
                if word in freq_table:
                    score += freq_table[word]
            sentence_scores[sentence] = score / max(1, len(sentence.split()))

        # Pick top sentences while preserving original order
        top_sentences = sorted(sentences, key=lambda s: sentence_scores.get(s, 0), reverse=True)[:max_sentences]
        ordered_summary = [s for s in sentences if s in top_sentences]
        return " ".join(ordered_summary)

    def summarize(self, text: str, max_sentences: int = 2) -> str:
        """
        Unified summarization pipeline:
        1. Hugging Face Pretrained Model
        2. Local Transformers Pipeline
        3. Google Gemini (if configured)
        4. Offline NLP Frequency Scoring
        """
        if not text or len(text.strip()) < 80:
            return text.strip()

        # 1. Hugging Face Pretrained
        hf_summary = self.summarize_huggingface(text)
        if hf_summary:
            return hf_summary

        # 2. Local Transformers pipeline
        local_summary = self.summarize_local_pipeline(text)
        if local_summary:
            return local_summary

        # 3. Gemini fallback if available
        if gemini_model.is_available():
            try:
                res = gemini_model.ask(f"Summarize this in {max_sentences} concise sentences:\n\n{text}")
                if res and not res.startswith("I ran into an issue"):
                    return res
            except Exception:
                pass

        # 4. Offline NLP extractive summarizer
        return self.summarize_extractive(text, max_sentences=max_sentences)


summarizer = HuggingFaceSummarizer()

def summarize(text: str, max_sentences: int = 2) -> str:
    return summarizer.summarize(text, max_sentences=max_sentences)
