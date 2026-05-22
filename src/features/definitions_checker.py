"""Regex-based checker for undefined capitalized multi-word terms.

The checker works in two passes:
1. Find the document's Definitions section and extract explicitly defined terms.
2. Scan the entire document for capitalized multi-word phrases and flag any
   that are used but never defined.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable


MULTI_WORD_TERM_PATTERN = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,})\b")
QUOTED_TERM_PATTERN = re.compile(
    r"(?P<term>[A-Z][A-Za-z0-9&'\-\/,\.]+(?:\s+[A-Z][A-Za-z0-9&'\-\/,\.]+){0,8})\s+(?:means|shall mean|refers to|has the meaning of)",
    re.IGNORECASE,
)
TERMED_PHRASE_PATTERN = re.compile(r"[\"\u201c\u201d](?P<term>[^\"\u201c\u201d]{2,120})[\"\u201c\u201d]\s+(?:means|shall mean|refers to|has the meaning of)", re.IGNORECASE)
SECTION_HEADING_PATTERN = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\s*)?(?P<title>[A-Z][A-Za-z0-9&'\-\/,\.\s]{2,80})\s*$"
)


@dataclass(frozen=True)
class UndefinedTermFinding:
    """A term used in the document but not found in the Definitions section."""

    term: str
    normalized_term: str
    context: str
    match_start: int
    match_end: int


@dataclass(frozen=True)
class DefinitionsCheckResult:
    """Structured result for the defined-terms audit."""

    defined_terms: dict[str, str] = field(default_factory=dict)
    used_terms: list[str] = field(default_factory=list)
    undefined_terms: list[UndefinedTermFinding] = field(default_factory=list)
    definitions_section_excerpt: str = ""

    @property
    def has_undefined_terms(self) -> bool:
        return bool(self.undefined_terms)


def check_defined_terms(document_text: str) -> DefinitionsCheckResult:
    """Run the two-pass defined-terms audit over an entire document text."""
    if not document_text:
        return DefinitionsCheckResult()

    paragraphs = _split_paragraphs(document_text)
    definitions_paragraphs, definitions_excerpt = _find_definitions_section(paragraphs)
    defined_terms = _extract_defined_terms(definitions_paragraphs)
    used_terms = _find_capitalized_terms(document_text)
    undefined_terms = _find_undefined_terms(document_text, defined_terms)

    return DefinitionsCheckResult(
        defined_terms=defined_terms,
        used_terms=used_terms,
        undefined_terms=undefined_terms,
        definitions_section_excerpt=definitions_excerpt,
    )


def _split_paragraphs(document_text: str) -> list[str]:
    normalized = document_text.replace("\r\n", "\n").replace("\r", "\n")
    raw_paragraphs = re.split(r"\n\s*\n+", normalized)
    paragraphs = [paragraph.strip() for paragraph in raw_paragraphs if paragraph.strip()]
    if paragraphs:
        return paragraphs
    return [line.strip() for line in normalized.split("\n") if line.strip()]


def _find_definitions_section(paragraphs: Iterable[str]) -> tuple[list[str], str]:
    collected: list[str] = []
    collecting = False

    for paragraph in paragraphs:
        cleaned = paragraph.strip()
        title = _extract_section_title(cleaned)

        if not collecting and title and "definitions" in title.lower():
            collecting = True
            collected.append(cleaned)
            continue

        if collecting:
            if _looks_like_next_section_heading(cleaned):
                break
            collected.append(cleaned)

    return collected, "\n\n".join(collected)


def _extract_section_title(paragraph: str) -> str | None:
    match = SECTION_HEADING_PATTERN.match(paragraph)
    if not match:
        return None
    return match.group("title").strip()


def _looks_like_next_section_heading(paragraph: str) -> bool:
    if not paragraph:
        return False

    if SECTION_HEADING_PATTERN.match(paragraph) and len(paragraph.split()) <= 12:
        return True

    if paragraph.isupper() and len(paragraph.split()) <= 8:
        return True

    return False


def _extract_defined_terms(paragraphs: Iterable[str]) -> dict[str, str]:
    defined_terms: dict[str, str] = {}

    for paragraph in paragraphs:
        for match in TERMED_PHRASE_PATTERN.finditer(paragraph):
            term = _normalize_term(match.group("term"))
            if term:
                defined_terms.setdefault(term, match.group("term").strip())

        for match in QUOTED_TERM_PATTERN.finditer(paragraph):
            term = _normalize_term(match.group("term"))
            if term:
                defined_terms.setdefault(term, match.group("term").strip())

        # Catch patterns like: Term means ...
        for candidate in MULTI_WORD_TERM_PATTERN.finditer(paragraph):
            term_text = candidate.group(1).strip()
            trailing = paragraph[candidate.end(): candidate.end() + 40].lower()
            if trailing.startswith(" means") or trailing.startswith(" shall mean"):
                normalized = _normalize_term(term_text)
                if normalized:
                    defined_terms.setdefault(normalized, term_text)

    return defined_terms


def _find_capitalized_terms(document_text: str) -> list[str]:
    matches = [match.group(1).strip() for match in MULTI_WORD_TERM_PATTERN.finditer(document_text)]
    unique_terms: list[str] = []
    seen: set[str] = set()

    for term in matches:
        # normalize and strip leading articles for consistency
        stripped = _strip_leading_article(term)
        normalized = _normalize_term(stripped)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_terms.append(stripped)

    return unique_terms


def _find_undefined_terms(document_text: str, defined_terms: dict[str, str]) -> list[UndefinedTermFinding]:
    findings: list[UndefinedTermFinding] = []
    allowed = set(defined_terms)

    for match in MULTI_WORD_TERM_PATTERN.finditer(document_text):
        term = match.group(1).strip()
        # remove leading articles like 'The Receiving Party' -> 'Receiving Party'
        stripped = _strip_leading_article(term)
        normalized = _normalize_term(stripped)
        if not normalized:
            continue

        if normalized in allowed:
            continue

        if _should_ignore_candidate(term):
            continue

        context = _extract_context(document_text, match.start(), match.end())
        findings.append(
            UndefinedTermFinding(
                term=stripped,
                normalized_term=normalized,
                context=context,
                match_start=match.start(),
                match_end=match.end(),
            )
        )

    # Deduplicate while preserving order.
    unique: list[UndefinedTermFinding] = []
    seen_terms: set[str] = set()
    for finding in findings:
        if finding.normalized_term in seen_terms:
            continue
        seen_terms.add(finding.normalized_term)
        unique.append(finding)
    return unique


def _normalize_term(term: str) -> str:
    cleaned = re.sub(r"\s+", " ", term).strip()
    cleaned = cleaned.strip("\"'()[]{}.,;:")
    return cleaned.lower()


def _strip_leading_article(term: str) -> str:
    return re.sub(r'^(?:the|a|an)\s+', '', term, flags=re.IGNORECASE).strip()


def _should_ignore_candidate(term: str) -> bool:
    lowered = term.lower()
    if any(token in lowered for token in ("section", "article", "exhibit", "schedule")):
        return True
    if lowered.startswith("state of ") or lowered.startswith("city of "):
        return True
    if lowered.startswith("united states"):
        return True
    return False


def _extract_context(document_text: str, start: int, end: int, window: int = 120) -> str:
    left = max(0, start - window)
    right = min(len(document_text), end + window)
    snippet = document_text[left:right].replace("\n", " ").strip()
    return re.sub(r"\s+", " ", snippet)


# Compatibility alias for consumers that want a more descriptive entry point.
find_undefined_terms = check_defined_terms
