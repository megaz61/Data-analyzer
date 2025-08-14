from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
from dotenv import load_dotenv
import numpy as np # Tambahkan import numpy

# Import from correct paths
from app.models.schemas import FileUploadResponse, ChatMessage, ChatResponse
from app.services.file_processor import EnhancedFileProcessor
from app.services.rag_service import GeminiRAGService

# Load environment variables
load_dotenv()

# Fungsi utilitas untuk mengkonversi tipe data NumPy ke Python
def convert_numpy_types(data):
    """Recursively convert numpy types to native Python types."""
    if isinstance(data, dict):
        return {k: convert_numpy_types(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(i) for i in data]
    elif isinstance(data, np.int64):
        return int(data)
    elif isinstance(data, np.float64):
        return float(data)
    elif isinstance(data, (np.ndarray, np.generic)):
        # Convert NumPy arrays and other types to lists or appropriate Python types
        return data.tolist()
    return data

app = FastAPI(title="Enhanced AI Data Analysis API", version="2.0.0")

# CORS middleware
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize enhanced services
file_processor = EnhancedFileProcessor()
processed_files = {}

# Initialize RAG service
try:
    rag_service = GeminiRAGService()
    RAG_AVAILABLE = True
    print("✅ RAG Service initialized successfully with Gemini")
except Exception as e:
    print(f"❌ RAG Service initialization failed: {e}")
    print("Chat functionality will be limited to basic analysis")
    rag_service = None
    RAG_AVAILABLE = False

@app.get("/")
async def root():
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
    return {
        "message": "Enhanced AI Data Analysis API is running",
        "status": "healthy",
        "version": "2.0.0",
        "model": model_name,
        "supported_formats": [".csv", ".xlsx", ".xls", ".pdf"],
        "features": [
            "Enhanced file type detection",
            "Advanced column type analysis",
            "Data quality assessment",
            "PDF document statistics & AI summarization",
            "RAG-powered chat interface"
        ]
    }

@app.get("/health")
async def health_check():
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
        "rag_available": RAG_AVAILABLE,
        "model_info": {
            "llm_model": model_name,
            "embedding_model": os.getenv("GEMINI_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
            "provider": "Google Gemini"
        },
        "services": {
            "file_processor": "ready",
            "rag_service": "ready" if RAG_AVAILABLE else "not available"
        },
        "supported_formats": file_processor.supported_formats,
        "new_features": {
            "file_detection": "Enhanced file type and structure detection",
            "column_analysis": "Automatic column type detection with confidence scores",
            "data_quality": "Comprehensive data quality assessment",
            "pdf_analysis": "Detailed PDF statistics with AI-powered summarization"
        }
    }

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Enhanced file upload and processing with detailed analysis"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in file_processor.supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Supported formats: {', '.join(file_processor.supported_formats)}"
            )

        print(f"Processing enhanced file: {file.filename} ({file_ext})")

        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        try:
            file_data = file_processor.process_file(tmp_path, file.filename)
            print(f"File processed successfully with enhanced features: {file_data['file_id']}")
            
            # Tambahkan konversi tipe data NumPy
            cleaned_file_data = convert_numpy_types(file_data)
            
            if RAG_AVAILABLE and rag_service:
                try:
                    file_id = rag_service.create_vector_store(cleaned_file_data)
                    cleaned_file_data["rag_available"] = True
                    print(f"✅ RAG vector store created: {file_id}")
                except Exception as e:
                    print(f"⚠️ RAG processing failed: {e}")
                    cleaned_file_data["rag_available"] = False
            else:
                cleaned_file_data["rag_available"] = False

            file_id = cleaned_file_data['file_id']
            processed_files[file_id] = cleaned_file_data

            return FileUploadResponse(
                filename=file.filename,
                file_id=file_id,
                message="File processed successfully with enhanced analysis",
                analysis_summary=cleaned_file_data.get('analysis_summary', {}),
                file_detection=cleaned_file_data.get('file_detection', {}),
                processing_info=cleaned_file_data.get('processing_info', {})
            )

        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced upload failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Enhanced chat with AI about uploaded data"""
    try:
        if not chat_message.file_id:
            raise HTTPException(status_code=400, detail="file_id is required")

        if chat_message.file_id not in processed_files:
            raise HTTPException(status_code=404, detail="File not found")

        if not RAG_AVAILABLE or not rag_service:
            file_data = processed_files[chat_message.file_id]
            basic_info = f"""RAG service tidak tersedia. Namun, saya dapat memberikan informasi dasar tentang file '{file_data['filename']}':

📊 Informasi File:
- Tipe: {file_data.get('type', 'Unknown').upper()}
- Status: Berhasil diproses dengan analisis enhanced

"""
            analysis = file_data.get('analysis_summary', {})
            if file_data.get('type') == 'csv':
                if 'shape' in analysis:
                    basic_info += f"- Dimensi: {analysis['shape'][0]} baris, {analysis['shape'][1]} kolom\n"
                if 'data_quality' in analysis:
                    basic_info += f"- Skor Kualitas Data: {analysis['data_quality'].get('data_quality_score', 'N/A')}/100\n"
            elif file_data.get('type') == 'pdf':
                if 'pages' in analysis:
                    basic_info += f"- Halaman: {analysis['pages']}\n"
                if 'word_count' in analysis:
                    basic_info += f"- Jumlah Kata: {analysis['word_count']:,}\n"

            basic_info += "\nUntuk analisis mendalam, pastikan RAG service aktif."

            return ChatResponse(
                response=basic_info,
                sources=[]
            )

        result = rag_service.query(chat_message.file_id, chat_message.message)
        return ChatResponse(
            response=result["response"],
            sources=result["sources"]
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Enhanced chat failed: {str(e)}")

@app.get("/file/{file_id}")
async def get_file_info(file_id: str):
    """Get enhanced file information"""
    if file_id not in processed_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Ambil data yang sudah bersih dari tipe NumPy
    file_data = processed_files[file_id]
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")

    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "type": file_data["type"],
        "analysis_summary": file_data.get("analysis_summary", {}),
        "file_detection": file_data.get("file_detection", {}),
        "processing_info": file_data.get("processing_info", {}),
        "processed_at": file_data.get("processed_at"),
        "rag_available": file_data.get("rag_available", False),
        "model_info": model_name,
        "enhanced_features": {
            "column_type_detection": "column_types" in file_data.get("analysis_summary", {}),
            "data_quality_assessment": "data_quality" in file_data.get("analysis_summary", {}),
            "ai_summary": "ai_summary" in file_data.get("analysis_summary", {}),
            "detailed_statistics": True
        }
    }
    
@app.get("/files")
async def list_files():
    """List all processed files with enhanced info"""
    return {
        "files": [
            {
                "file_id": file_id,
                "filename": data["filename"],
                "type": data["type"],
                "processed_at": data.get("processed_at"),
                "file_size_mb": data.get("file_detection", {}).get("size_mb", 0),
                "rag_available": data.get("rag_available", False),
                "has_enhanced_analysis": "analysis_summary" in data,
                "quality_score": data.get("analysis_summary", {}).get("data_quality", {}).get("data_quality_score"),
            }
            for file_id, data in processed_files.items()
        ],
        "total_files": len(processed_files),
        "supported_formats": file_processor.supported_formats
    }

@app.get("/file/{file_id}/detection")
async def get_file_detection(file_id: str):
    """Get detailed file detection information"""
    if file_id not in processed_files:
        raise HTTPException(status_code=404, detail="File not found")

    file_data = processed_files[file_id]
    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "file_detection": file_data.get("file_detection", {}),
        "supported": file_data.get("file_detection", {}).get("is_supported", False)
    }

@app.get("/file/{file_id}/quality")
async def get_data_quality(file_id: str):
    """Get detailed data quality assessment"""
    if file_id not in processed_files:
        raise HTTPException(status_code=404, detail="File not found")

    file_data = processed_files[file_id]
    analysis = file_data.get("analysis_summary", {})

    if "data_quality" not in analysis:
        raise HTTPException(status_code=404, detail="Data quality assessment not available for this file type")

    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "data_quality": analysis["data_quality"],
        "column_types": analysis.get("column_types", {}),
        "recommendations": {
            "high_null_columns": "Consider removing or imputing columns with >50% missing data",
            "duplicates": "Review and remove duplicate rows if appropriate",
            "data_types": "Verify detected column types match your expectations"
        }
    }

@app.get("/model-info")
async def get_model_info():
    """Get current model information with enhanced features"""
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
    return {
        "llm_model": model_name,
        "embedding_model": os.getenv("GEMINI_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        "provider": "Google Gemini",
        "model_url": f"https://ai.google.dev/models/{model_name}",
        "api_version": "2.0.0",
        "supported_file_types": file_processor.supported_formats,
        "capabilities": [
            "Enhanced file type detection",
            "Advanced column type analysis",
            "Data quality assessment",
            "PDF document statistics",
            "AI-powered PDF summarization",
            "Indonesian language support",
            "Question answering with RAG",
            "Interactive data visualization",
            "Multi-sheet Excel analysis"
        ],
        "new_features": [
            "Automatic encoding detection for CSV files",
            "Confidence scores for column type detection",
            "Comprehensive data quality metrics",
            "PDF reading time estimation",
            "Email, URL, phone number detection",
            "Boolean and categorical data recognition"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Enhanced AI Data Analysis API v2.0.0")
    print(f"📊 Supported formats: {file_processor.supported_formats}")
    print("🔧 Enhanced features: File detection, Column analysis, Data quality, PDF summarization")
    uvicorn.run(app, host="0.0.0.0", port=8000)