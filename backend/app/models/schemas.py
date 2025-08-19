# app/models/schemas.py
from __future__ import annotations
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    type: str
    analysis_summary: Optional[Dict[str, Any]] = None
    preview: Optional[Dict[str, Any]] = None
    processing_info: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="ignore")

class ProcessedFile(BaseModel):
    file_id: str
    filename: str
    type: str
    analysis_summary: Optional[Dict[str, Any]] = None
    vector_store_id: Optional[str] = None
    processing_info: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(extra="ignore")

class ChatRequest(BaseModel):
    file_id: str = Field(..., alias="fileId")
    user_message: str = Field(..., alias="message")
    top_k: int = 3
    temperature: float = 0.2
    top_p: float = 0.9
    max_output_tokens: int = 768
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

class ChatResponse(BaseModel):
    answer: Optional[str] = None
    response: Optional[str] = None
    sources: Optional[List[Union[str, Dict[str, Any]]]] = None
    used_top_k: Optional[int] = None
    model: Optional[str] = None
    model_config = ConfigDict(extra="ignore")
