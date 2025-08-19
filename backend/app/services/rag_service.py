# app/services/rag_service.py
from __future__ import annotations
import os
from typing import List, Dict, Any
import numpy as np
from dotenv import load_dotenv

# Pastikan .env terbaca walau urutan import tidak ideal
load_dotenv(override=True)

# -------- Embedding (kecil & cepat) --------
try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

def _embed_model():
    name = os.getenv("EMBED_MODEL") or os.getenv("GEMINI_EMBEDDING_MODEL") \
           or "sentence-transformers/all-MiniLM-L6-v2"
    if SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer(name)
    except Exception:
        return None

# -------- Gemini --------
def _gemini_model():
    api = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api:
        return None
    import google.generativeai as genai
    genai.configure(api_key=api)
    return genai.GenerativeModel(os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"))

def _cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-9)
    b = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-9)
    return a @ b.T

def _shrink(s: str, max_chars: int) -> str:
    s = (s or "").strip().replace("\r", "")
    return s if len(s) <= max_chars else s[:max_chars]

class GeminiRAGService:
    """Satu pintu ke Gemini: vector store ringan + prompt terstruktur, hemat token."""
    def __init__(self) -> None:
        self.stores: Dict[str, Dict[str, Any]] = {}
        self.embedder = _embed_model()
        self.model    = _gemini_model()
        self.model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

    # ----- Embedding -----
    def _embed(self, texts: List[str]) -> np.ndarray:
        if self.embedder is None:
            return np.zeros((len(texts), 384), dtype=np.float32)
        arr = self.embedder.encode(texts, convert_to_numpy=True)
        return arr.astype(np.float32)

    # ----- Build vector store -----
    def create_vector_store(self, file_id: str, payload: Dict[str, Any]) -> str:
        chunks = payload.get("text_chunks") or []
        clean = [_shrink((c or "").replace("\n\n", "\n"), 700) for c in chunks if c and c.strip()]
        clean = clean[:120] or ["(no content)"]
        emb = self._embed(clean)
        self.stores[file_id] = {"chunks": clean, "emb": emb}
        return f"vs-{file_id}"

    # ----- Retrieve -----
    def _retrieve(self, file_id: str, query: str, k: int = 3) -> List[str]:
        store = self.stores.get(file_id)
        if not store: return []
        chunks: List[str] = store["chunks"]
        sims = _cosine(self._embed([query]), store["emb"]).ravel()
        idx = np.argsort(-sims)[:max(1, k)]
        return [chunks[i] for i in idx]

    # ----- Prompt builder (padat & berdaging) -----
    def _build_prompt(self, context_blocks: List[str], question: str) -> str:
        ctx = "\n---\n".join(_shrink(c, 600) for c in context_blocks)
        return (
            "Jawab sebagai analis data senior (Bahasa Indonesia). "
            "Fokus pada ringkasan padat, angka, dan rekomendasi.\n\n"
            "[FORMAT]\n"
            "1) Ringkasan Kunci (3–5 poin)\n"
            "2) Bukti & Angka (kutip kolom/angka dari konteks)\n"
            "3) Rekomendasi Praktis (2–4 butir)\n"
            "Jika konteks kurang memadai, sebutkan keterbatasannya.\n\n"
            f"[PERTANYAAN]\n{_shrink(question, 400)}\n\n"
            f"[KONTEKS]\n{_shrink(ctx, 1800)}\n\nJawaban:"
        )

    # ----- Call Gemini -----
    def _call_gemini(self, prompt: str) -> str:
        if self.model is None:
            return "Model AI tidak tersedia. Set GEMINI_API_KEY terlebih dulu."
        try:
            resp = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": float(os.getenv("CHAT_TEMPERATURE", "0.25")),
                    "top_p": float(os.getenv("CHAT_TOP_P", "0.95")),
                    "max_output_tokens": int(os.getenv("CHAT_MAX_TOKENS")),
                },
            )
            return (getattr(resp, "text", None) or "").strip() or "Tidak ada jawaban."
        except Exception as e:
            return f"Terjadi error saat memanggil Gemini: {e}"

    # ----- Public chat -----
    def chat(self, file_id: str, user_message: str, top_k: int = 3) -> Dict[str, Any]:
        top_k = max(1, min(top_k, 5))
        ctx = self._retrieve(file_id, user_message, k=top_k)
        prompt = self._build_prompt(ctx, user_message)
        answer = self._call_gemini(prompt)
        sources = [{"snippet": _shrink(c, 300)} for c in ctx]
        return {"answer": answer, "sources": sources, "used_top_k": top_k, "model": self.model_name if self.model else "none"}
