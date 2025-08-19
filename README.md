# Data Assistant — AI-Powered Document Analysis & Q&A 📊🤖

**Data Assistant** is a web app that helps you understand **PDF / CSV / Excel** without writing code.  
Upload a file → get **automatic summaries**, **data quality checks**, **chart suggestions**, and **ask anything** about the document via AI.

> Goal: let non-technical users “talk” to their data—fast.
---

```markdown

```markdown
## 🖼️ Screenshots & Demo

### 🤖 AI Chat Assistant
<div align="center">
  <img src="Result and Example_dataset/Result/chat-assistData.png" 
       alt="AI Chat Assistant Interface" 
       width="500">
</div>

### 📊 CSV Descriptive Results

<div align="center">

| | |
|:---:|:---:|
| <img src="Result and Example_dataset/Result/descriptive-result-csv1.jpg" alt="CSV Result 1" width="400"> | <img src="Result and Example_dataset/Result/descriptive-result-csv2.jpg" alt="CSV Result 2" width="400"> |

</div>

<div align="center">
  <img src="Result and Example_dataset/Result/descriptive-result-csv3.jpg" 
       alt="CSV Result 3" 
       width="450">
</div>

### 📁 Upload Interface
<div align="center">
  <img src="Result and Example_dataset/Result/upload-data-page.png" 
       alt="Upload Data Interface" 
       width="450">
</div>

```

## ✨ Key Features

- 🔍 **Automatic Summary**  
  PDF: page/word count, reading time, longest paragraph, metadata.  
  CSV/Excel: basic stats, dtypes, unique values, null %, etc.
- ✅ **Data Quality Check**  
  Detect high-null columns, duplicates, and a simple quality score.
- 📈 **Smart Chart Suggestions**  
  Histogram, Bar, Line/Area, Scatter, Pie — chosen automatically based on data patterns.
- 💬 **AI Chat (RAG)**  
  Answers are grounded in **your document’s content** (not hallucinated).

---

## 🧠 Tech Stack & Roles

- **Frontend**: **Next.js + Tailwind CSS** — UI for upload, summaries, charts, and chat  
- **Charting**: **Recharts** — interactive charts from backend specs  
- **Backend**: **FastAPI (Python)** — endpoints for upload, analysis, and chat  
- **Tabular Data**: **Pandas + NumPy** — stats, null %, duplicates, dtypes  
- **PDF**: **PyPDF2** — text & metadata extraction  
- **Excel**: **openpyxl/xlrd** — read xlsx/xls

### 🔎 RAG (Retrieval-Augmented Generation)
A strategy to keep answers **relevant & document-grounded**:
1) **Ingest** content/analysis → split into small **chunks**  
2) **Embed** each chunk via `sentence-transformers/all-MiniLM-L6-v2` (384-dim vectors)  
3) Retrieve **Top-K** similar chunks via **cosine similarity**  
4) Ask **Gemini 1.5 Flash** to answer using those chunks as context

### 🧩 Embeddings — `all-MiniLM-L6-v2`
Turns text into numerical vectors so we can measure **semantic similarity**.  
Lightweight & fast — great for a server-side RAG prototype.

### 🤖 LLM — Gemini 1.5 Flash
Used for:
- **PDF summarization** → stored at `analysis_summary.ai_summary`  
- **Chat responses** → grounded with retrieved context

```markdown


---

## 📦 Project Structure (compact)

```
data-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models/schemas.py
│   │   └── services/
│   │       ├── file_processor.py
│   │       ├── rag_service.py
│   │       └── data_analyzer.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── public/
│   │   └── favicon.ico
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx
│   │   │   └── page.tsx
│   │   ├── components/
│   │   │   ├── Chat.tsx
│   │   │   ├── DataVisualization.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   └── lib/
│   │       ├── api.ts
│   │       └── types/
│   │           └── index.ts
│   ├── .env
│   ├── .next/
│   ├── node_modules/
│   ├── package.json
│   └── package-lock.json
```

---

## 🚀 Getting Started (Local Dev)

### ✅ Prerequisites
- **Python 3.11+** (recommended)  
- **Node.js 18+** & **npm**  
- **Gemini API Key** (optional but recommended)

### 1) Backend (FastAPI)

**a) Create virtual env & install dependencies**

> **Windows (PowerShell)**
```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt
```

> **macOS/Linux**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt
```

**b) Configure `.env`**

Create `backend/.env`:

```ini
# --- AI / LLM ---
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash

# --- Server ---
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000"]

# (optional)
ENVIRONMENT=development
```

**c) Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000`  
Swagger: `http://localhost:8000/docs`

---

### 2) Frontend (Next.js)

**a) Install dependencies**
```bash
cd frontend
npm install
# If your project doesn't include these yet:
# npm i recharts lucide-react
```

**b) Configure `.env.local`**
```ini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**c) Run dev server**
```bash
npm run dev
```

App: `http://localhost:3000`

---

## 🧪 Usage (Quick Flow)

1) Open `http://localhost:3000`  
2) Upload **PDF/CSV/Excel** → view **summary** & **chart suggestions**  
3) Use **Chat** to ask questions about the document

> API alternative:
> - `POST /upload` — upload a file  
> - `GET /file/{id}` — get detailed info (incl. `analysis_summary`)  
> - `POST /chat` — RAG chat (`file_id` + `message`)

Sample cURL upload:
```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/file.pdf"
```

---

## 🔧 Tips & Troubleshooting

- **PDF AI summary not visible in UI**  
  Ensure the frontend fetches **file details** via `GET /file/{id}` (not only `/files`), because `analysis_summary` is returned in the detail endpoint.
- **Chat lacks context**  
  Check `.env` → `GEMINI_API_KEY` must be set; verify RAG indexing logs (embeddings & vector store created).
- **Charts not rendering / Recharts errors**  
  Ensure `recharts` is installed and components wait for data readiness.
- **CORS errors**  
  Add `http://localhost:3000` (or your domain) to `CORS_ORIGINS`.

---

---

Built with ❤️ by **Ega**.  
If this helps you, please ⭐ the repo!
