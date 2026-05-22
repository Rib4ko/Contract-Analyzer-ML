"""Clause-to-playbook similarity scoring.

The default backend is TF-IDF cosine similarity to avoid downloading heavy
models at startup. A SentenceTransformer backend can be enabled explicitly if a
small local model is already available in the environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


SimilarityBackend = Literal["tfidf", "sentence-transformers"]


@dataclass(frozen=True)
class SimilarityResult:
    """Structured similarity output for a single clause comparison."""

    incoming_clause: str
    playbook_clause: str
    similarity_score: float
    similarity_percentage: float
    backend: str
    is_match: bool


class PlaybookSimilarityEngine:
    """Compare contract clauses against a reference playbook clause."""

    def __init__(
        self,
        backend: SimilarityBackend = "tfidf",
        sentence_transformer_model: str = "all-MiniLM-L6-v2",
        match_threshold: float = 0.80,
    ) -> None:
        self.backend = backend
        self.sentence_transformer_model = sentence_transformer_model
        self.match_threshold = match_threshold
        self._reference_clause: str | None = None
        self._sentence_model = None
        # Cached vectorizer and reference vector for TF-IDF backend to avoid
        # refitting for each incoming clause when comparing many clauses.
        self._tfidf_vectorizer = None
        self._tfidf_reference_vector = None

    def set_reference_clause(self, playbook_clause: str) -> None:
        """Cache the playbook clause so many incoming clauses can reuse it."""
        self._reference_clause = playbook_clause

    def compare(self, incoming_clause: str, playbook_clause: str | None = None) -> SimilarityResult:
        """Compare one clause against a playbook clause and return a percentage."""
        reference_clause = playbook_clause or self._reference_clause
        if not reference_clause:
            raise ValueError("A playbook clause must be supplied before comparing clauses.")

        if self.backend == "sentence-transformers":
            embeddings = self._encode([incoming_clause, reference_clause])
            score = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])
        else:
            # If we have a cached vectorizer and reference vector for the
            # currently set reference clause, reuse it to avoid refitting on
            # every compare call.
            if self._tfidf_vectorizer is not None and self._reference_clause == reference_clause:
                matrix_incoming = self._tfidf_vectorizer.transform([incoming_clause])
                ref_vec = self._tfidf_reference_vector
                score = float(cosine_similarity(matrix_incoming, ref_vec)[0][0])
            else:
                vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
                matrix = vectorizer.fit_transform([incoming_clause, reference_clause])
                score = float(cosine_similarity(matrix[0:1], matrix[1:2])[0][0])
                # Cache vectorizer and reference vector for future comparisons
                try:
                    self._tfidf_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
                    self._tfidf_vectorizer.fit([reference_clause])
                    self._tfidf_reference_vector = self._tfidf_vectorizer.transform([reference_clause])
                    self._reference_clause = reference_clause
                except Exception:
                    # Caching is a best-effort optimization; silently skip on any issue
                    self._tfidf_vectorizer = None
                    self._tfidf_reference_vector = None

        score = max(0.0, min(1.0, score))
        return SimilarityResult(
            incoming_clause=incoming_clause,
            playbook_clause=reference_clause,
            similarity_score=score,
            similarity_percentage=round(score * 100.0, 2),
            backend=self.backend,
            is_match=score >= self.match_threshold,
        )

    def _encode(self, texts: list[str]) -> np.ndarray:
        if self.backend == "sentence-transformers":
            return self._encode_sentence_transformers(texts)
        return self._encode_tfidf(texts)

    def _encode_tfidf(self, texts: list[str]) -> np.ndarray:
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
        matrix = vectorizer.fit_transform(texts)
        return matrix

    def _encode_sentence_transformers(self, texts: list[str]) -> np.ndarray:
        model = self._load_sentence_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return np.asarray(embeddings)

    @lru_cache(maxsize=1)
    def _load_sentence_model(self):  # pragma: no cover - optional dependency path
        try:
            from sentence_transformers import SentenceTransformer
        except Exception as exc:  # pragma: no cover - optional dependency path
            raise RuntimeError(
                "sentence-transformers is not installed; use the default tfidf backend instead."
            ) from exc

        return SentenceTransformer(self.sentence_transformer_model)


_default_similarity_engine = PlaybookSimilarityEngine()


def compare_clause_to_playbook(
    incoming_clause: str,
    playbook_clause: str,
    *,
    backend: SimilarityBackend = "tfidf",
    match_threshold: float = 0.80,
) -> SimilarityResult:
    """Convenience function for one-off clause comparisons."""
    engine = PlaybookSimilarityEngine(backend=backend, match_threshold=match_threshold)
    return engine.compare(incoming_clause, playbook_clause)
