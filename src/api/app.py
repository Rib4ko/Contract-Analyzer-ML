"""FastAPI application for contract analysis and DOCX export."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.features.docx_export import export_audit_to_docx
from src.pipeline.analyzer import LegalDocumentAnalyzer
from src.ingest.pdf_parser import extract_pdf_paragraphs
from src.models.router import get_router_model
from src.api.security import verify_jwt
import filetype

MAX_FILE_SIZE = 10 * 1024 * 1024

class ExportRequest(BaseModel):
    analysis: dict[str, Any] = Field(default_factory=dict)
    title: str | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="Legal ML API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/parse_playbook", dependencies=[Depends(verify_jwt)])
    async def parse_playbook(playbook_file: UploadFile = File(...)) -> dict[str, str]:
        if not playbook_file.filename:
            raise HTTPException(status_code=400, detail="A file is required.")
        
        content = await playbook_file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
            
        playbook_suffix = Path(playbook_file.filename).suffix.lower()
        playbook_mapping = {}

        if playbook_suffix == '.json':
            import json
            try:
                playbook_mapping = json.loads(content)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid playbook JSON format.")
        elif playbook_suffix == '.txt':
            text_content = content.decode('utf-8', errors='ignore')
            paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
            router = get_router_model()
            for p in paragraphs:
                cat = router.classify(p).label_name
                if cat.lower() != "other":
                    playbook_mapping[cat] = p
        elif playbook_suffix == '.pdf':
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tp:
                tp.write(content)
                tp_path = Path(tp.name)
            try:
                paragraphs = extract_pdf_paragraphs(tp_path, min_words=8)
                router = get_router_model()
                for p in paragraphs:
                    cat = router.classify(p.text).label_name
                    if cat.lower() != "other":
                        playbook_mapping[cat] = p.text
            finally:
                tp_path.unlink(missing_ok=True)
        else:
            raise HTTPException(status_code=400, detail="Playbook must be .json, .txt, or .pdf")

        return playbook_mapping

    @app.post("/api/analyze", dependencies=[Depends(verify_jwt)])
    async def analyze_document(
        file: UploadFile = File(...),
        playbook_clause: str | None = Form(None),
        playbook_mapping: str | None = Form(None),
        minimum_words_per_clause: int = Form(8),
        scan_mode: str = Form("text"),
        ocr_language: str = Form("en"),
        air_gapped_mode: bool = Form(False)
    ) -> dict[str, Any]:
        if not file.filename:
            raise HTTPException(status_code=400, detail="A file is required.")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large. Max 10MB.")
            
        kind = filetype.guess(content)
        if kind and kind.mime not in ["application/pdf", "image/png", "image/jpeg", "image/tiff"]:
            raise HTTPException(status_code=415, detail="Unsupported file format. Use PDF or Images.")

        suffix = Path(file.filename).suffix.lower()
        if suffix not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif']:
            raise HTTPException(status_code=415, detail="Unsupported file extension.")

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.close()
        temp_path = Path(temp_file.name)
        
        try:
            with open(temp_path, "wb") as f:
                f.write(content)

            mapping_dict = None
            if playbook_mapping:
                import json
                try:
                    mapping_dict = json.loads(playbook_mapping)
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid playbook mapping JSON format.")

            analyzer = LegalDocumentAnalyzer(minimum_words_per_clause=minimum_words_per_clause)
            
            # Privacy Toggle: Disable Groq API extraction entirely
            qa_questions_param = {} if air_gapped_mode else None
            
            analysis = analyzer.analyze(
                temp_path,
                playbook_clause=playbook_clause,
                playbook_clause_by_category=mapping_dict,
                scan_mode=scan_mode,
                ocr_language=ocr_language,
                qa_questions=qa_questions_param,
            )
            return analysis.to_dict()
        finally:
            temp_path.unlink(missing_ok=True)

    @app.post("/api/export", dependencies=[Depends(verify_jwt)])
    def export_report(payload: ExportRequest, background_tasks: BackgroundTasks) -> FileResponse:
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        output_temp.close()
        output_file = Path(output_temp.name)
        report_title = payload.title or "Legal Contract Audit Report"

        export_audit_to_docx(payload.analysis, output_file, title=report_title)
        background_tasks.add_task(output_file.unlink, missing_ok=True)

        filename = f"{report_title.lower().replace(' ', '-')}-report.docx"
        return FileResponse(
            path=output_file,
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            background=background_tasks,
        )

    return app


app = create_app()