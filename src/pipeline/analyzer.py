"""Master orchestration layer for contract analysis.

This module coordinates PDF ingestion, contract routing, entity extraction,
lightweight QA, playbook deviation checks, and defined-terms auditing into a
single structured result object.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.entities.ner import extract_organizations, extract_jurisdictions
from src.features.definitions_checker import DefinitionsCheckResult, check_defined_terms
from src.features.playbook_similarity import (
    PlaybookSimilarityEngine,
    SimilarityResult,
)
from src.ingest.pdf_parser import (
    ExtractedParagraph,
    extract_pdf_paragraphs,
    extract_pdf_paragraphs_with_mode,
    extract_pdf_text,
)
from src.models.qa import QAExtractor
from src.models.router import ClassificationResult, RouterModel, get_router_model


@dataclass(frozen=True)
class ClauseAnalysis:
    """Structured analysis for one clause/paragraph."""

    page: int
    text: str
    category: str
    label_index: int
    entities: list[str] = field(default_factory=list)
    jurisdictions: list[str] = field(default_factory=list)
    organizations: list[str] = field(default_factory=list)
    qa_answers: dict[str, str] = field(default_factory=dict)
    playbook_similarity: float | None = None
    playbook_similarity_backend: str | None = None
    risk_flags: list[str] = field(default_factory=list)
    undefined_terms: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DocumentAnalysis:
    """Document-level output for downstream API or export use."""

    source_file: str
    generated_at: str
    findings: list[ClauseAnalysis]
    undefined_terms: list[dict[str, Any]]
    definitions_result: DefinitionsCheckResult
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "generated_at": self.generated_at,
            "findings": [asdict(finding) for finding in self.findings],
            "undefined_terms": list(self.undefined_terms),
            "definitions_result": {
                "defined_terms": dict(self.definitions_result.defined_terms),
                "used_terms": list(self.definitions_result.used_terms),
                "undefined_terms": [asdict(item) for item in self.definitions_result.undefined_terms],
                "definitions_section_excerpt": self.definitions_result.definitions_section_excerpt,
            },
            "summary": dict(self.summary),
        }


_DEFAULT_QA_QUESTIONS: dict[str, str] = {
    "payment": "When is payment due?",
    "fees": "What amount is payable?",
    "term": "What is the term or duration?",
    "renewal": "Does the clause include automatic renewal?",
    "termination": "What termination notice or trigger is specified?",
}


class LegalDocumentAnalyzer:
    """End-to-end contract analysis pipeline."""

    def __init__(
        self,
        router_model: RouterModel | None = None,
        qa_extractor: QAExtractor | None = None,
        playbook_backend: str = "tfidf",
        playbook_match_threshold: float = 0.80,
        minimum_words_per_clause: int = 8,
    ) -> None:
        self.router_model = router_model or get_router_model()
        self.qa_extractor = qa_extractor or QAExtractor()
        self.playbook_backend = playbook_backend
        self.playbook_match_threshold = playbook_match_threshold
        self.minimum_words_per_clause = minimum_words_per_clause

    def analyze(
        self,
        pdf_path: str | Path,
        *,
        scan_mode: str = "text",
        ocr_language: str = "en",
        playbook_clause: str | None = None,
        playbook_clause_by_category: Mapping[str, str] | None = None,
        qa_questions: Mapping[str, str] | None = None,
    ) -> DocumentAnalysis:
        """Run the full pipeline and return a structured audit payload."""
        pdf_path = Path(pdf_path)
        if scan_mode == "ocr":
            paragraphs = extract_pdf_paragraphs_with_mode(
                pdf_path,
                min_words=self.minimum_words_per_clause,
                scan_mode=scan_mode,
                ocr_language=ocr_language,
            )
            full_text = extract_pdf_text(pdf_path, scan_mode=scan_mode, ocr_language=ocr_language)
        else:
            paragraphs = extract_pdf_paragraphs(pdf_path, min_words=self.minimum_words_per_clause)
            full_text = extract_pdf_text(pdf_path)
        definitions_result = check_defined_terms(full_text)
        playbook_engine = PlaybookSimilarityEngine(
            backend=self.playbook_backend,
            match_threshold=self.playbook_match_threshold,
        )

        findings: list[ClauseAnalysis] = []
        undefined_by_normalized = {item.normalized_term: item for item in definitions_result.undefined_terms}
        qa_questions = dict(qa_questions or _DEFAULT_QA_QUESTIONS)

        for paragraph in paragraphs:
            classification = self.router_model.classify(paragraph.text)
            categories = self._determine_categories(classification)
            jurisdictions = self._extract_jurisdictions(categories, paragraph.text)
            organizations = self._extract_organizations(categories, paragraph.text)
            qa_answers = self._extract_qa_answers(classification.label_name, paragraph.text, qa_questions)
            playbook_similarity = None
            playbook_backend = None
            risk_flags: list[str] = []

            reference_clause = self._select_playbook_clause(classification.label_name, playbook_clause, playbook_clause_by_category)
            if reference_clause:
                similarity_result = playbook_engine.compare(paragraph.text, reference_clause)
                playbook_similarity = similarity_result.similarity_percentage
                playbook_backend = similarity_result.backend
                if not similarity_result.is_match:
                    risk_flags.append(
                        f"Playbook deviation ({similarity_result.similarity_percentage:.2f}% similarity)"
                    )

            undefined_terms = self._find_undefined_terms_in_clause(paragraph.text, undefined_by_normalized)
            if undefined_terms:
                risk_flags.append("Undefined defined-term usage")

            if classification.label_name.lower().find("govern") >= 0 and not jurisdictions:
                risk_flags.append("Governing law clause missing explicit jurisdiction")

            findings.append(
                ClauseAnalysis(
                    page=paragraph.page,
                    text=paragraph.text,
                    category=classification.label_name,
                    label_index=classification.label_index,
                    entities=sorted(set(jurisdictions + organizations)),
                    jurisdictions=jurisdictions,
                    organizations=organizations,
                    qa_answers=qa_answers,
                    playbook_similarity=playbook_similarity,
                    playbook_similarity_backend=playbook_backend,
                    risk_flags=risk_flags,
                    undefined_terms=undefined_terms,
                )
            )

        summary = self._build_summary(findings, definitions_result)
        return DocumentAnalysis(
            source_file=str(pdf_path),
            generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            findings=findings,
            undefined_terms=[asdict(item) for item in definitions_result.undefined_terms],
            definitions_result=definitions_result,
            summary=summary,
        )

    def _determine_categories(self, classification: ClassificationResult) -> list[str]:
        return [classification.label_name]

    def _extract_jurisdictions(self, categories: list[str], text: str) -> list[str]:
        lower_categories = [category.lower() for category in categories]
        if any("govern" in category or "law" in category for category in lower_categories):
            return extract_jurisdictions(text)
        return []

    def _extract_organizations(self, categories: list[str], text: str) -> list[str]:
        lower_categories = [category.lower() for category in categories]
        if any("part" in category or "party" in category for category in lower_categories):
            return extract_organizations(text)
        return []

    def _extract_qa_answers(
        self,
        category_name: str,
        text: str,
        qa_questions: Mapping[str, str],
    ) -> dict[str, str]:
        lower_category = category_name.lower()
        answers: dict[str, str] = {}

        if "payment" not in lower_category and "term" not in lower_category:
            return answers

        for keyword, question in qa_questions.items():
            if keyword in lower_category:
                result = self.qa_extractor.ask(question, text)
                if result.answer:
                    answers[question] = result.answer
        return answers

    def _select_playbook_clause(
        self,
        category_name: str,
        default_clause: str | None,
        clause_by_category: Mapping[str, str] | None,
    ) -> str | None:
        if clause_by_category:
            for key, value in clause_by_category.items():
                if key.lower() in category_name.lower():
                    return value
        return default_clause

    def _find_undefined_terms_in_clause(
        self,
        clause_text: str,
        undefined_terms: Mapping[str, Any],
    ) -> list[str]:
        found: list[str] = []
        for normalized_term, finding in undefined_terms.items():
            if finding.term and finding.term.lower() in clause_text.lower():
                found.append(finding.term)
        return _unique_preserve_order(found)

    def _build_summary(self, findings: list[ClauseAnalysis], definitions_result: DefinitionsCheckResult) -> dict[str, Any]:
        high_risk = sum(1 for finding in findings if finding.risk_flags)
        similarity_scores = [finding.playbook_similarity for finding in findings if finding.playbook_similarity is not None]
        average_similarity = round(sum(similarity_scores) / len(similarity_scores), 2) if similarity_scores else None
        return {
            "total_clauses": len(findings),
            "high_risk_clauses": high_risk,
            "undefined_terms": len(definitions_result.undefined_terms),
            "average_playbook_similarity": average_similarity,
            "risk_posture": self._derive_risk_posture(high_risk, len(definitions_result.undefined_terms)),
        }

    def _derive_risk_posture(self, high_risk: int, undefined_terms: int) -> str:
        if high_risk >= 5 or undefined_terms >= 10:
            return "High"
        if high_risk >= 1 or undefined_terms >= 1:
            return "Moderate"
        return "Low"


class ContractAnalysisService:
    """Small facade for callers that want a single method name."""

    def __init__(self, analyzer: LegalDocumentAnalyzer | None = None) -> None:
        self.analyzer = analyzer or LegalDocumentAnalyzer()

    def analyze_pdf(self, pdf_path: str | Path, **kwargs: Any) -> DocumentAnalysis:
        return self.analyzer.analyze(pdf_path, **kwargs)


def analyze_contract_pdf(pdf_path: str | Path, **kwargs: Any) -> DocumentAnalysis:
    """Convenience function for notebook and API usage."""
    return LegalDocumentAnalyzer().analyze(pdf_path, **kwargs)


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
