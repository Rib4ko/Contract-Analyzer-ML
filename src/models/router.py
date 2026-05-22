"""Lazy inference wrapper for the pre-trained contract SVM router.

This module only loads pre-trained artifacts from ``models/``. It does not
contain any training code.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import joblib


@dataclass(frozen=True)
class ClassificationResult:
    """Structured classification output for a single paragraph."""

    paragraph: str
    label_index: int
    label_name: str
    raw_prediction: Any


class RouterModel:
    """Lazily loads and serves the contract classification model.

    The expected on-disk artifacts are:
    - ``models/contract_svm_model.pkl``
    - ``models/label_list.pkl``

    The loaded model is assumed to be a scikit-learn estimator or pipeline that
    exposes ``predict``.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        label_list_path: str | Path | None = None,
    ) -> None:
        project_root = Path(__file__).resolve().parents[2]
        models_dir = project_root / "models"

        self.model_path = Path(model_path) if model_path else models_dir / "contract_svm_model.pkl"
        self.label_list_path = (
            Path(label_list_path) if label_list_path else models_dir / "label_list.pkl"
        )

        self._model: Any | None = None
        self._label_list: list[str] | None = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None and self._label_list is not None

    @property
    def label_list(self) -> list[str]:
        self._ensure_loaded()
        assert self._label_list is not None
        return self._label_list

    @property
    def model(self) -> Any:
        self._ensure_loaded()
        return self._model

    def load(self) -> "RouterModel":
        """Load the serialized model and labels from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Missing router model artifact: {self.model_path}")
        if not self.label_list_path.exists():
            raise FileNotFoundError(f"Missing label list artifact: {self.label_list_path}")

        self._model = joblib.load(self.model_path)
        loaded_labels = joblib.load(self.label_list_path)

        if isinstance(loaded_labels, dict):
            # Accept either {index: label} or {label: index}; normalize below.
            if all(isinstance(key, int) for key in loaded_labels.keys()):
                ordered = [loaded_labels[index] for index in sorted(loaded_labels)]
            else:
                ordered = list(loaded_labels)
            self._label_list = [str(label) for label in ordered]
        else:
            self._label_list = [str(label) for label in list(loaded_labels)]

        return self

    def classify(self, paragraph: str) -> ClassificationResult:
        """Classify a single paragraph and return the human-readable label."""
        if paragraph is None:
            raise ValueError("paragraph must not be None")

        self._ensure_loaded()
        assert self._model is not None
        assert self._label_list is not None

        raw_prediction = self._model.predict([paragraph])[0]
        label_index, label_name = self._resolve_prediction(raw_prediction)
        return ClassificationResult(
            paragraph=paragraph,
            label_index=label_index,
            label_name=label_name,
            raw_prediction=raw_prediction,
        )

    def classify_many(self, paragraphs: Iterable[str]) -> list[ClassificationResult]:
        return [self.classify(paragraph) for paragraph in paragraphs]

    def predict(self, paragraphs: Sequence[str]) -> list[str]:
        """Compatibility method that returns only label names."""
        return [result.label_name for result in self.classify_many(paragraphs)]

    def _ensure_loaded(self) -> None:
        if not self.is_loaded:
            self.load()

    def _resolve_prediction(self, raw_prediction: Any) -> tuple[int, str]:
        assert self._label_list is not None

        # Common sklearn outputs: Python ints, NumPy scalars, or strings.
        if isinstance(raw_prediction, str):
            if raw_prediction in self._label_list:
                return self._label_list.index(raw_prediction), raw_prediction
            return -1, raw_prediction

        try:
            label_index = int(raw_prediction)
        except (TypeError, ValueError):
            raw_text = str(raw_prediction)
            if raw_text in self._label_list:
                return self._label_list.index(raw_text), raw_text
            return -1, raw_text

        if 0 <= label_index < len(self._label_list):
            return label_index, self._label_list[label_index]
        return label_index, str(raw_prediction)


_default_router_model: RouterModel | None = None


def get_router_model() -> RouterModel:
    """Return a cached RouterModel instance for app-wide reuse."""
    global _default_router_model
    if _default_router_model is None:
        _default_router_model = RouterModel()
    return _default_router_model
