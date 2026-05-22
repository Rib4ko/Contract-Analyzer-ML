"""Document ingestion and paragraph extraction helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pdfplumber
import numpy as np
from PIL import Image


ScanMode = str


@dataclass(frozen=True)
class ExtractedParagraph:
    page: int
    text: str


def extract_pdf_paragraphs(pdf_path: str | Path, min_words: int = 8) -> list[ExtractedParagraph]:
    """Extract cleaned paragraph candidates from a PDF using pdfplumber."""
    return extract_pdf_paragraphs_with_mode(pdf_path, min_words=min_words, scan_mode="text")


def extract_pdf_paragraphs_with_mode(
    pdf_path: str | Path,
    min_words: int = 8,
    scan_mode: ScanMode = "text",
    ocr_language: str = "en",
) -> list[ExtractedParagraph]:
    """Extract cleaned paragraph candidates from a PDF or image using text extraction or OCR."""
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    paragraphs: list[ExtractedParagraph] = []
    page_texts = _extract_page_texts(pdf_path, scan_mode=scan_mode, ocr_language=ocr_language)

    for page_number, text in enumerate(page_texts, start=1):
        for paragraph in _split_page_text(text):
            clean_text = _clean_paragraph(paragraph)
            if len(clean_text.split()) < min_words:
                continue
            paragraphs.append(ExtractedParagraph(page=page_number, text=clean_text))
    return paragraphs


def extract_pdf_text(pdf_path: str | Path, scan_mode: ScanMode = "text", ocr_language: str = "en") -> str:
    """Return the full extracted text for a PDF."""
    chunks: list[str] = []
    for page_text in _extract_page_texts(Path(pdf_path), scan_mode=scan_mode, ocr_language=ocr_language):
        if page_text:
            chunks.append(page_text)
    return "\n\n".join(chunks)


def _extract_page_texts(pdf_path: Path, scan_mode: ScanMode, ocr_language: str) -> list[str]:
    if scan_mode == "ocr" or pdf_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        return _extract_page_texts_with_ocr(pdf_path, ocr_language=ocr_language)

    chunks: list[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            chunks.append(text or "")
    return chunks


def _extract_page_texts_with_ocr(pdf_path: Path, ocr_language: str) -> list[str]:
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(
            "OCR scan mode requires PyMuPDF (pymupdf). Install optional OCR dependencies first."
        ) from exc

    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(
            "OCR scan mode requires PaddleOCR. Install optional OCR dependencies first."
        ) from exc

    ocr = PaddleOCR(use_angle_cls=True, lang=ocr_language, show_log=False)
    page_texts: list[str] = []

    if pdf_path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
        image = Image.open(pdf_path).convert("RGB")
        image_array = np.asarray(image)
        ocr_result = ocr.ocr(image_array, cls=True)
        page_texts.append(_flatten_paddleocr_result(ocr_result))
        return page_texts

    document = fitz.open(str(pdf_path))
    for page in document:
        pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        image_array = np.asarray(image)
        ocr_result = ocr.ocr(image_array, cls=True)
        page_texts.append(_flatten_paddleocr_result(ocr_result))

    document.close()
    return page_texts


def _split_page_text(text: str) -> Iterable[str]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for chunk in normalized.split("\n\n"):
        chunk = chunk.strip()
        if chunk:
            yield chunk


def _clean_paragraph(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def _flatten_paddleocr_result(ocr_result: object) -> str:
    lines: list[str] = []
    if not ocr_result:
        return ""

    if isinstance(ocr_result, list):
        for item in ocr_result:
            if isinstance(item, list):
                for line in item:
                    if isinstance(line, (list, tuple)) and len(line) >= 2:
                        text = line[1][0] if isinstance(line[1], (list, tuple)) else line[1]
                        if text:
                            lines.append(str(text))
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                text = item[1][0] if isinstance(item[1], (list, tuple)) else item[1]
                if text:
                    lines.append(str(text))

    return "\n".join(lines)
