"""CLI entrypoint for contract analysis and Word export."""
from __future__ import annotations

import argparse
from pathlib import Path
import logging

from src.features.docx_export import export_audit_to_docx
from src.pipeline.analyzer import LegalDocumentAnalyzer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze a contract PDF and export findings to Word.")
    parser.add_argument("pdf_path", type=Path, help="Path to the input contract PDF")
    parser.add_argument(
        "--output-docx",
        type=Path,
        default=None,
        help="Optional path for the exported Word report",
    )
    parser.add_argument(
        "--playbook-clause",
        type=str,
        default=None,
        help="Reference playbook clause used for deviation scoring",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=8,
        help="Minimum words required for a paragraph to be analyzed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    analyzer = LegalDocumentAnalyzer(minimum_words_per_clause=args.min_words)
    analysis = analyzer.analyze(
        args.pdf_path,
        playbook_clause=args.playbook_clause,
    )

    logger = logging.getLogger("legal_ml.cli")
    logging.basicConfig(level=logging.INFO)
    logger.info("Source: %s", analysis.source_file)
    logger.info("Clauses: %s", analysis.summary.get("total_clauses", 0))
    logger.info("High-risk clauses: %s", analysis.summary.get("high_risk_clauses", 0))
    logger.info("Undefined terms: %s", analysis.summary.get("undefined_terms", 0))

    if args.output_docx:
        export_audit_to_docx(analysis.to_dict(), args.output_docx)
        logger.info("Word report written to: %s", args.output_docx)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
