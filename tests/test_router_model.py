from __future__ import annotations

from dataclasses import dataclass

import joblib

from src.models.router import RouterModel


@dataclass
class DummyModel:
    prediction: int

    def predict(self, rows):
        return [self.prediction for _ in rows]


def test_router_model_loads_serialized_artifacts(tmp_path) -> None:
    model_path = tmp_path / "contract_svm_model.pkl"
    label_path = tmp_path / "label_list.pkl"

    joblib.dump(DummyModel(prediction=2), model_path)
    joblib.dump(["Alpha", "Beta", "Gamma"], label_path)

    router = RouterModel(model_path=model_path, label_list_path=label_path)
    result = router.classify("This clause is just a test.")

    assert result.label_index == 2
    assert result.label_name == "Gamma"
