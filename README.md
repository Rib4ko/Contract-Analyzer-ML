# Legal ML

Quickstart

1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .\venv
.\venv\Scripts\activate
```

2. Install required packages (pinned scikit-learn to match model artifact):

```powershell
.\venv\Scripts\python -m pip install -r requirements.txt
```

3. Run the CLI smoke test (example):

```powershell
@'
from src.models.router import RouterModel
from src.features.definitions_checker import check_defined_terms
from src.features.playbook_similarity import compare_clause_to_playbook

router = RouterModel()
print('router_loaded_before', router.is_loaded)
result = router.classify('This Agreement shall be governed by the laws of Delaware.')
print('router_label', result.label_name)

defs = check_defined_terms(
    'Definitions\n\n"Confidential Information" means all non-public information.\n\n'
    'The Receiving Party shall protect the Confidential Information and the Proprietary Materials.'
)
print('undefined_terms', [f.term for f in defs.undefined_terms])

sim = compare_clause_to_playbook(
    'The Receiving Party shall keep all Confidential Information strictly confidential.',
    'The Receiving Party must keep Confidential Information confidential and not disclose it.'
)
print('similarity', sim.similarity_percentage)
'@ | .\venv\Scripts\python -
```

Notes

- `scikit-learn` is pinned to `1.6.1` to match the pre-serialized model in `models/` and avoid unpickle warnings.
- Heavy/optional packages (transformers, sentence-transformers, torch) are listed in `requirements.txt` as comments; install them only if you need semantic similarity or large-model QA features.
- OCR scanning is available as an optional mode. Use the `scan_mode` option in the API or UI to switch between `text` and `ocr`. Install `paddleocr` and `pymupdf` from `requirements-optional.txt` if you want scanned PDFs to be read with OCR.
- To expose an API, consider running the `src/pipeline/analyzer.py` logic behind a FastAPI app (not wired by default).

## Project overview

This repository provides a lightweight, local-first contract audit pipeline that performs three core tasks useful to U.S. transactional lawyers:

- Playbook deviation detection (clause similarity)
- Defined-terms validation (detects capitalized terms that are used but not defined)
- Microsoft Word export of findings (consumer-friendly `.docx` report)

The tools are intentionally designed to avoid heavy external APIs and to work with pre-serialized, local models placed in the `models/` folder.

## Key features

- **Playbook Deviation (Similarity):** Uses a TF‑IDF cosine similarity engine by default to compare a detected clause against a firm "playbook" clause and reports a similarity percentage and match flag. Optional sentence-transformers support exists if you install the heavier dependencies.
- **Defined Terms Checker:** Two-pass regex + normalization that extracts the `Definitions` section and flags capitalized multi-word terms that are used but not defined.
- **Word Export:** Generates a readable `.docx` report with findings, risk callouts, and undefined-term tables using `python-docx`.

## Architecture (high level)

The codebase is modular and split into clear responsibilities. The main components are:

- **Ingest:** `src/ingest/pdf_parser.py` — PDF text/paragraph extraction (pdfplumber).
- **Routing / Classification:** `src/models/router.py` — lazy loader for the pre-trained SVM router pipeline (expects artifacts in `models/`).
- **Features:** `src/features/` — business logic modules:
    - `playbook_similarity.py` — clause similarity engine
    - `definitions_checker.py` — defined-terms validator
    - `docx_export.py` — `.docx` report generator
- **Orchestration:** `src/pipeline/analyzer.py` — wires ingestion, routing, feature checks, and export together and returns a `DocumentAnalysis` result object.
- **CLI / UX:** `src/cli/main.py` — small command-line entry for quick runs.

## Folder structure (important files)

- `models/` — Put your pre-trained artifacts here (`contract_svm_model.pkl`, `label_list.pkl`).
- `src/pipeline/analyzer.py` — Orchestration and `LegalDocumentAnalyzer`.
- `src/models/router.py` — Router lazy loader.
- `src/features/playbook_similarity.py` — Similarity engine.
- `src/features/definitions_checker.py` — Defined-terms checker.
- `src/features/docx_export.py` — Word export utilities.
- `tests/` — Unit tests used during development.

## How it works (simple flow)

1. Ingest the PDF and split into paragraphs.
2. For each significant paragraph, the `RouterModel` classifies the clause type.
3. If a playbook clause is provided for that type, the playbook engine computes similarity and flags deviations.
4. The definitions checker scans the whole document and marks capitalized terms used but not defined.
5. The analyzer compiles findings into a `DocumentAnalysis` and you can export it to `.docx` via `export_audit_to_docx()`.

## Quick links / examples

- Use the playbook similarity helper: `from src.features.playbook_similarity import compare_clause_to_playbook` ([src/features/playbook_similarity.py](src/features/playbook_similarity.py)).
- Export a report: `from src.features.docx_export import export_audit_to_docx` ([src/features/docx_export.py](src/features/docx_export.py)).
- Run the analyzer: `from src.pipeline.analyzer import analyze_contract_pdf` ([src/pipeline/analyzer.py](src/pipeline/analyzer.py)).

## Next steps

- If you'd like a tiny web API, I can scaffold a FastAPI app that exposes `analyze_contract_pdf` and triggers `export_audit_to_docx`.
- If you want exact model compatibility, we can reserialize the router model on a machine matching the desired `scikit-learn` version.
## Frontend UI

The previous React-based frontend has been removed from this repository. If you want a new UI scaffolded, I can create a fresh Vite + React + Tailwind starter—tell me your preferred visual direction.

## Backend API

The FastAPI app is implemented in `src/api/app.py` and exposes endpoints for analysis and DOCX export.

Run the backend locally:

```powershell
python -m venv .\venv
.\venv\Scripts\Activate
python -m pip install -r requirements.txt
uvicorn src.api.app:app --reload --port 8001
```

Health check: `GET /health` returns a simple `{"status":"ok"}` JSON.

API endpoints:
- `POST /api/analyze` — multipart upload, accepts `file` and form fields (`playbook_clause`, `minimum_words_per_clause`, `scan_mode`, `ocr_language`).
- `POST /api/export` — JSON body with analysis payload to receive a `.docx` file.

## Run tests

Run the unit tests with `pytest`:

```powershell
Set-Location .
pytest -q
```

## Notes & Next steps

- `scikit-learn` is pinned to `1.6.1` to match the pre-serialized model artifacts in `models/`.
- Optional OCR support requires `paddleocr` and `pymupdf` (listed in `requirements-optional.txt`).
- Consider adding CI (GitHub Actions) to run tests and linting. I can add a minimal workflow for you.

---
Updated README to reflect the removed frontend and to add run/test instructions.
"# Contract-Analyzer-ML" 
