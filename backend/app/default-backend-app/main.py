from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import tempfile
from dotenv import load_dotenv

# Import from correct paths
from app.models.schemas import FileUploadResponse, ChatMessage, ChatResponse
from app.services.file_processor import FileProcessor
from app.services.rag_service import GeminiRAGService  # Updated import

# Load environment variables
load_dotenv()

app = FastAPI(title="AI Data Analysis API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
file_processor = FileProcessor()
processed_files = {}

# Initialize RAG service
try:
    rag_service = GeminiRAGService()  # Updated to use Gemini
    RAG_AVAILABLE = True
    print("✅ RAG Service initialized successfully with Gemini")
except Exception as e:
    print(f"❌ RAG Service initialization failed: {e}")
    print("Chat functionality will be limited to basic analysis")
    rag_service = None
    RAG_AVAILABLE = False

@app.get("/")
async def root():
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")  # Updated
    return {
        "message": "AI Data Analysis API is running", 
        "status": "healthy",
        "model": model_name
    }

@app.get("/health")
async def health_check():
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")  # Updated
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),  # Updated
        "rag_available": RAG_AVAILABLE,
        "model_info": {
            "llm_model": model_name,  # Updated
            "embedding_model": os.getenv("GEMINI_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),  # Updated
            "provider": "Google Gemini"  # Updated
        },
        "services": {
            "file_processor": "ready",
            "rag_service": "ready" if RAG_AVAILABLE else "not available"
        }
    }

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and process file"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        print(f"Processing file: {file.filename}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process file
            file_data = file_processor.process_file(tmp_path, file.filename)
            print(f"File processed successfully: {file_data['file_id']}")
            
            # Process with RAG if available
            if RAG_AVAILABLE and rag_service:
                try:
                    file_id = rag_service.create_vector_store(file_data)
                    file_data["rag_available"] = True
                    print(f"✅ RAG vector store created: {file_id}")
                except Exception as e:
                    print(f"⚠️ RAG processing failed: {e}")
                    file_data["rag_available"] = False
            else:
                file_data["rag_available"] = False
            
            # Store processed data
            file_id = file_data['file_id']
            processed_files[file_id] = file_data
            
            return FileUploadResponse(
                filename=file.filename,
                file_id=file_id,
                message="File processed successfully",
                analysis_summary=file_data.get('analysis', {})
            )
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Chat with AI about uploaded data"""
    try:
        if not chat_message.file_id:
            raise HTTPException(status_code=400, detail="file_id is required")
        
        if chat_message.file_id not in processed_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        if not RAG_AVAILABLE or not rag_service:
            file_data = processed_files[chat_message.file_id]
            return ChatResponse(
                response=f"RAG service tidak tersedia. Namun, saya dapat melihat file '{file_data['filename']}' telah diproses. Analisis dasar tersedia dalam informasi file.",
                sources=[]
            )
        
        result = rag_service.query(chat_message.file_id, chat_message.message)
        return ChatResponse(
            response=result["response"],
            sources=result["sources"]
        )
    
    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/file/{file_id}")
async def get_file_info(file_id: str):
    """Get file information"""
    if file_id not in processed_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_data = processed_files[file_id]
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")  # Updated
    
    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "type": file_data["type"],
        "analysis": file_data.get("analysis", {}),
        "rag_available": file_data.get("rag_available", False),
        "model_info": model_name
    }

@app.get("/files")
async def list_files():
    """List all processed files"""
    return {
        "files": [
            {
                "file_id": file_id,
                "filename": data["filename"],
                "type": data["type"],
                "rag_available": data.get("rag_available", False)
            }
            for file_id, data in processed_files.items()
        ]
    }

@app.get("/model-info")
async def get_model_info():
    """Get current model information"""
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")  # Updated
    return {
        "llm_model": model_name,
        "embedding_model": os.getenv("GEMINI_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),  # Updated
        "provider": "Google Gemini",  # Updated
        "model_url": f"https://ai.google.dev/models/{model_name}",  # Updated
        "capabilities": [
            "Text generation",
            "Data analysis", 
            "Indonesian language support",
            "Question answering",
            "Instruction following",
            "RAG support",
            "Multi-modal understanding"  # Added Gemini capability
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)