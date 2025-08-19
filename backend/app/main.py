# app/main.py
from __future__ import annotations
import io, os, uuid
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# load .env seawal mungkin (sebelum import service yang baca ENV)
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import FileUploadResponse, ChatRequest, ChatResponse, ProcessedFile
from app.services.data_analyzer import DataAnalyzer
from app.services.rag_service import GeminiRAGService

app = FastAPI(title="AI Data Assistant Backend", version="1.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

analyzer = DataAnalyzer()
rag = GeminiRAGService()  # punya rag.model (Gemini) & embedder
PROCESSED_FILES: Dict[str, ProcessedFile] = {}

def _gen_id() -> str: return uuid.uuid4().hex
def _safe_text(b: bytes) -> str:
    try: return b.decode("utf-8", errors="ignore")
    except Exception: return ""

# ------- Robust PDF text extraction -------
def _extract_pdf_pages_as_text(content: bytes) -> List[str]:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = [(p.extract_text() or "") for p in pdf.pages]
        if any(pages): return pages
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(content))
        pages = [(p.extract_text() or "") for p in r.pages]
        if any(pages): return pages
    except Exception:
        pass
    try:
        import PyPDF2
        r = PyPDF2.PdfReader(io.BytesIO(content))
        pages = [(p.extract_text() or "") for p in r.pages]
        if any(pages): return pages
    except Exception:
        pass
    raise HTTPException(status_code=500, detail="Unable to extract text from PDF")

@app.get("/", include_in_schema=False)
def root(): return {"ok": True}

# ===================== UPLOAD =====================
@app.post("/upload", response_model=FileUploadResponse)
async def upload(file: UploadFile = File(...)):
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_id = _gen_id()
    name = file.filename
    lower = name.lower()
    content = await file.read()

    # ---- CSV ----
    if lower.endswith(".csv") or file.content_type in ("text/csv",):
        df = pd.read_csv(io.BytesIO(content))
        analysis = analyzer.analyze_dataframe(df)

        preview_csv = df.head(200).to_csv(index=False)
        rag.create_vector_store(file_id, {
            "type": "csv",
            "text_chunks": [f"Columns: {', '.join(df.columns.astype(str))}", preview_csv]
        })

        resp = FileUploadResponse(
            file_id=file_id, filename=name, type="csv", analysis_summary=analysis,
            processing_info={"rows": int(df.shape[0]), "cols": int(df.shape[1]), "vector_store_id": f"vs-{file_id}"}
        )

    # ---- Excel ----
    elif lower.endswith((".xlsx", ".xls")) or file.content_type in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","application/vnd.ms-excel"):
        df = pd.read_excel(io.BytesIO(content))
        analysis = analyzer.analyze_dataframe(df)

        preview_csv = df.head(200).to_csv(index=False)
        rag.create_vector_store(file_id, {
            "type": "excel",
            "text_chunks": [f"Columns: {', '.join(df.columns.astype(str))}", preview_csv]
        })

        resp = FileUploadResponse(
            file_id=file_id, filename=name, type="excel", analysis_summary=analysis,
            processing_info={"rows": int(df.shape[0]), "cols": int(df.shape[1]), "vector_store_id": f"vs-{file_id}"}
        )

    # ---- PDF (dengan summary, metadata, extraction_info) ----
    elif lower.endswith(".pdf") or file.content_type in ("application/pdf",):
        # 1) Extract text per halaman
        pages_text = _extract_pdf_pages_as_text(content)
        full_text = "\n".join(pages_text)

        # 2) Info per halaman & total halaman
        page_infos = [{"word_count": len((p or "").split())} for p in pages_text]
        total_pages = int(len(pages_text))
        pages_with_text = int(sum(1 for p in page_infos if p.get("word_count", 0) > 0))

        # 3) Metadata
        file_size_bytes = len(content)
        metadata = {
            "type": "pdf",
            "pages": total_pages,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
            "extractable": total_pages > 0,
        }

        # 4) Ringkasan pada upload (bisa OFF via PDF_SUMMARY_ON_UPLOAD=0)
        do_summary = os.getenv("PDF_SUMMARY_ON_UPLOAD", "1") != "0"
        pdf_result = analyzer.analyze_pdf(
            full_text=full_text,
            page_texts=page_infos,
            metadata=metadata,
            gemini_model=rag.model if do_summary else None,
            do_summary=do_summary,
        )

        # Pastikan field alias yang dibutuhkan UI terisi (hindari N/A)
        pdf_result.setdefault("pages", total_pages)
        pdf_result.setdefault("page_count", total_pages)
        pdf_result.setdefault("metadata", metadata)
        if "extraction_info" not in pdf_result:
            pdf_result["extraction_info"] = {}
        pdf_result["extraction_info"].update({
            "pages_with_text": pages_with_text,
            "total_pages": total_pages,     # dipakai sebagian UI
            "pages_total": total_pages,     # alias lain
            "success_rate": round((pages_with_text / max(1, total_pages)) * 100, 1),
        })

        # 5) Vector store (chunk pendek agar hemat)
        chunks = [ (t or "").strip().replace("\r", "").replace("\n\n", "\n")[:800] for t in pages_text ]
        chunks = [c for c in chunks if c][:60]
        rag.create_vector_store(file_id, {"type": "pdf", "text_chunks": chunks})

        # 6) Response
        resp = FileUploadResponse(
            file_id=file_id, filename=name, type="pdf",
            analysis_summary=pdf_result,
            preview={"first_1000_chars": full_text[:1000]},
            processing_info={"pages": total_pages, "vector_store_id": f"vs-{file_id}"},
        )

    # ---- TXT / lainnya ----
    else:
        text = _safe_text(content)
        stats = analyzer._pdf_statistics(text, [{"word_count": len(text.split())}])
        chunks = [text[i:i+700] for i in range(0, min(len(text), 35000), 700)]
        rag.create_vector_store(file_id, {"type": "txt", "text_chunks": chunks})

        resp = FileUploadResponse(
            file_id=file_id, filename=name, type="txt", analysis_summary=stats,
            preview={"first_1000_chars": text[:1000]},
            processing_info={"chars": len(text), "vector_store_id": f"vs-{file_id}"},
        )

    PROCESSED_FILES[file_id] = ProcessedFile(
        file_id=resp.file_id, filename=resp.filename, type=resp.type,
        analysis_summary=resp.analysis_summary,
        vector_store_id=resp.processing_info.get("vector_store_id"),
        processing_info=resp.processing_info,
    )
    return resp

# ===================== CHAT =====================
async def _chat_core(req: ChatRequest) -> ChatResponse:
    if req.file_id not in PROCESSED_FILES:
        raise HTTPException(status_code=404, detail="file_id not found")
    pack = rag.chat(
        file_id=req.file_id,
        user_message=req.user_message,
        top_k=max(1, min(req.top_k or 3, 5)),  # hemat
    )
    return ChatResponse(
        answer=pack.get("answer"),
        sources=pack.get("sources"),
        used_top_k=pack.get("used_top_k"),
        model=pack.get("model"),
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_api(req: ChatRequest): return await _chat_core(req)

@app.post("/chat", response_model=ChatResponse)
async def chat_alias(req: ChatRequest): return await _chat_core(req)

# ===================== FILE GET =====================
@app.get("/file/{file_id}", response_model=ProcessedFile)
async def get_file(file_id: str):
    file = PROCESSED_FILES.get(file_id)
    if not file: raise HTTPException(status_code=404, detail="file not found")
    return file
