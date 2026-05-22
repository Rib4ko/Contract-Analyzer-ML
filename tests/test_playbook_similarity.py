from __future__ import annotations

from src.features.playbook_similarity import compare_clause_to_playbook


def test_playbook_similarity_scores_related_clauses_higher() -> None:
    playbook_clause = "The Receiving Party shall keep all Confidential Information strictly confidential."
    similar_clause = "The Receiving Party must keep Confidential Information confidential and not disclose it."
    different_clause = "This Agreement shall be governed by the laws of Delaware."

    similar_result = compare_clause_to_playbook(similar_clause, playbook_clause)
    different_result = compare_clause_to_playbook(different_clause, playbook_clause)

    assert similar_result.similarity_percentage > different_result.similarity_percentage
    assert 0.0 <= similar_result.similarity_percentage <= 100.0
    assert 0.0 <= different_result.similarity_percentage <= 100.0
