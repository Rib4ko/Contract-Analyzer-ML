"""Lightweight QA extraction adapters.

The production workspace defaults to a no-download, heuristic-first approach so
local laptops do not need to pull a large transformer model on startup. If a
caller wants to plug in a Hugging Face QA pipeline, it can be injected through
``qa_pipeline``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

import re


@dataclass(frozen=True)
class QAResult:
    question: str
    answer: str | None
    score: float | None = None
    source: str = "heuristic"


import os
import json
import urllib.request
import urllib.error

class QAExtractor:
    """QA adapter using Groq API."""

    def __init__(self, groq_api_key: str | None = None) -> None:
        self.groq_api_key = groq_api_key or os.environ.get("GROQ_API_KEY", "")

    def ask(self, question: str, context: str) -> QAResult:
        if self.groq_api_key:
            return self._ask_with_groq(question, context)
        return self._ask_with_heuristics(question, context)

    def _ask_with_groq(self, question: str, context: str) -> QAResult:
        prompt = f"Context: {context}\n\nQuestion: {question}\n\nAnswer concisely (in 5 words or less). If the answer is not in the context, output 'None'."
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 50,
        }
        
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                result_data = json.loads(response.read().decode('utf-8'))
                answer = result_data['choices'][0]['message']['content'].strip()
                if answer.lower().startswith("none") or not answer:
                    answer = None
                return QAResult(
                    question=question,
                    answer=answer,
                    score=1.0,
                    source="groq",
                )
        except urllib.error.URLError:
            return self._ask_with_heuristics(question, context)

    def _ask_with_heuristics(self, question: str, context: str) -> QAResult:
        lowered_question = question.lower()

        if "payment" in lowered_question or "due date" in lowered_question:
            answer = _extract_payment_like_phrase(context)
            return QAResult(question=question, answer=answer, source="heuristic")

        if "term" in lowered_question or "duration" in lowered_question:
            answer = _extract_term_like_phrase(context)
            return QAResult(question=question, answer=answer, source="heuristic")

        answer = _extract_sentence_with_keywords(context, lowered_question)
        return QAResult(question=question, answer=answer, source="heuristic")


_DATE_PATTERN = re.compile(
    r"\b(?:on\s+)?(?:the\s+)?(?:(?:\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+)?[A-Z][a-z]+\s+\d{1,2},\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})\b"
)
_AMOUNT_PATTERN = re.compile(
    r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\b(?:thirty|sixty|ninety)\s+days\b",
    re.IGNORECASE,
)
_TERM_PATTERN = re.compile(r"\b(?:for a period of|during the term of|for a term of)\s+([^.;]+)", re.IGNORECASE)


def _extract_payment_like_phrase(context: str) -> str | None:
    date_match = _DATE_PATTERN.search(context)
    if date_match:
        return date_match.group(0).strip()

    amount_match = _AMOUNT_PATTERN.search(context)
    if amount_match:
        return amount_match.group(0).strip()

    return _extract_sentence_with_keywords(context, "payment")


def _extract_term_like_phrase(context: str) -> str | None:
    term_match = _TERM_PATTERN.search(context)
    if term_match:
        return term_match.group(1).strip()
    return _extract_sentence_with_keywords(context, "term")


def _extract_sentence_with_keywords(context: str, keyword: str) -> str | None:
    sentences = re.split(r"(?<=[.!?])\s+", context)
    for sentence in sentences:
        if keyword in sentence.lower():
            return sentence.strip()
    return sentences[0].strip() if sentences else None
