from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

class FileDetection(BaseModel):
    extension: str
    size_bytes: int
    size_mb: float
    filename: str
    is_supported: bool
    type: str
    
    # CSV specific
    encoding: Optional[str] = None
    delimiter: Optional[str] = None
    estimated_columns: Optional[int] = None
    sample_lines: Optional[List[str]] = None
    
    # Excel specific
    sheet_count: Optional[int] = None
    sheet_names: Optional[List[str]] = None
    engine: Optional[str] = None
    sample_columns: Optional[List[str]] = None
    estimated_rows: Optional[int] = None
    
    # PDF specific
    page_count: Optional[int] = None
    is_encrypted: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    first_page_chars: Optional[int] = None
    estimated_extractable: Optional[bool] = None
    sample_text: Optional[str] = None
    
    error: Optional[str] = None

class ProcessingInfo(BaseModel):
    encoding_used: Optional[str] = None
    delimiter_used: Optional[str] = None
    total_rows_processed: Optional[int] = None

class ColumnTypeInfo(BaseModel):
    detected_type: str
    confidence: float
    pandas_dtype: str
    null_percentage: float
    unique_count: int
    sample_values: List[Any]
    additional_info: Dict[str, Any]

class DataQuality(BaseModel):
    completeness_percentage: float
    duplicate_rows: int
    duplicate_percentage: float
    high_null_columns: List[Dict[str, Union[str, float]]]
    data_quality_score: float

class ChartData(BaseModel):
    type: str
    bins: Optional[List[float]] = None
    counts: Optional[List[int]] = None
    stats: Optional[Dict[str, float]] = None
    categories: Optional[List[str]] = None
    total_unique: Optional[int] = None
    top_category_percentage: Optional[float] = None

class ExtractionInfo(BaseModel):
    total_pages_processed: int
    pages_with_text: int
    extraction_success_rate: float

class AnalysisSummary(BaseModel):
    # Common fields
    shape: Optional[List[int]] = None
    columns: Optional[List[str]] = None
    dtypes: Optional[Dict[str, str]] = None
    null_counts: Optional[Dict[str, int]] = None
    null_percentages: Optional[Dict[str, float]] = None
    summary_stats: Optional[Dict[str, Dict[str, float]]] = None
    charts: Optional[Dict[str, Dict[str, Any]]] = None
    
    # Enhanced CSV/Excel fields
    column_types: Optional[Dict[str, Dict[str, Any]]] = None
    data_quality: Optional[Dict[str, Any]] = None
    
    # Excel specific
    total_sheets: Optional[int] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    sheet_names: Optional[List[str]] = None
    sheets_quality_summary: Optional[Dict[str, Dict[str, Any]]] = None
    overall_quality_score: Optional[float] = None
    
    # PDF specific
    pages: Optional[int] = None
    word_count: Optional[int] = None
    char_count: Optional[int] = None
    char_count_no_spaces: Optional[int] = None
    paragraph_count: Optional[int] = None
    sentence_count: Optional[int] = None
    line_count: Optional[int] = None
    non_empty_lines: Optional[int] = None
    average_words_per_page: Optional[float] = None
    average_chars_per_page: Optional[float] = None
    longest_paragraph: Optional[int] = None
    average_paragraph_length: Optional[float] = None
    reading_time_minutes: Optional[float] = None
    ai_summary: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    extraction_info: Optional[Dict[str, Union[int, float]]] = None

class FileUploadResponse(BaseModel):
    filename: str
    file_id: str
    message: str
    analysis_summary: Dict[str, Any]  # Using Dict for flexibility
    file_detection: Optional[Dict[str, Any]] = None
    processing_info: Optional[Dict[str, Any]] = None

class ChatMessage(BaseModel):
    message: str
    file_id: str

class ChatResponse(BaseModel):
    response: str
    sources: List[str]

class EnhancedFileInfo(BaseModel):
    file_id: str
    filename: str
    type: str
    processed_at: Optional[str] = None
    file_size_mb: Optional[float] = None
    rag_available: bool
    has_enhanced_analysis: bool
    quality_score: Optional[float] = None

class FileAnalysisCapabilities(BaseModel):
    column_type_detection: bool
    data_quality_assessment: bool
    ai_summary: bool
    detailed_statistics: bool

class ModelInfo(BaseModel):
    llm_model: str
    embedding_model: str
    provider: str
    model_url: str
    api_version: str
    supported_file_types: List[str]
    capabilities: List[str]
    new_features: List[str]

class QualityAssessmentResponse(BaseModel):
    file_id: str
    filename: str
    data_quality: Dict[str, Any]
    column_types: Dict[str, Dict[str, Any]]
    recommendations: Dict[str, str]

class HealthCheckResponse(BaseModel):
    status: str
    gemini_configured: bool
    rag_available: bool
    model_info: Dict[str, str]
    services: Dict[str, str]
    supported_formats: List[str]
    new_features: Dict[str, str]

class RootResponse(BaseModel):
    message: str
    status: str
    version: str
    model: str
    supported_formats: List[str]
    features: List[str]