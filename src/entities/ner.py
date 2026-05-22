"""Lightweight spaCy-backed entity extraction helpers."""
from __future__ import annotations

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def load_spacy_model():  # pragma: no cover - optional dependency path
    """Load spaCy's small English model when available.

    The function intentionally falls back to a blank English pipeline if the
    pre-trained model is not installed so the workspace remains usable offline.
    """
    try:
        import spacy
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("spaCy is not installed") from exc

    try:
        return spacy.load("en_core_web_sm")
    except Exception:
        return spacy.blank("en")


def extract_jurisdictions(text: str) -> list[str]:
    """Extract geopolitical entities from a clause."""
    try:
        nlp = load_spacy_model()
    except Exception:
        return []

    doc = nlp(text)
    jurisdictions = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
    return _unique_preserve_order(jurisdictions)


def extract_organizations(text: str) -> list[str]:
    """Extract organization names from a clause."""
    try:
        nlp = load_spacy_model()
    except Exception:
        return []

    doc = nlp(text)
    organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    return _unique_preserve_order(organizations)


def _unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
