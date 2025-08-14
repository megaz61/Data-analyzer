from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class FileUploadResponse(BaseModel):
    filename: str
    file_id: str
    message: str
    analysis_summary: Dict[str, Any]

class ChatMessage(BaseModel):
    message: str
    file_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    sources: List[str] = []