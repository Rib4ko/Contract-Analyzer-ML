from __future__ import annotations

from src.features.definitions_checker import check_defined_terms


def test_defined_terms_checker_flags_undefined_multi_word_terms() -> None:
    text = (
        "Definitions\n\n"
        '"Confidential Information" means all non-public information.\n\n'
        "The Receiving Party shall protect the Confidential Information and the Proprietary Materials."
    )

    result = check_defined_terms(text)

    assert "confidential information" in result.defined_terms
    assert any(finding.term == "Receiving Party" for finding in result.undefined_terms)
    assert any(finding.term == "Proprietary Materials" for finding in result.undefined_terms)
