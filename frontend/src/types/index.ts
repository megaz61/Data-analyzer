// Enhanced types for the AI Data Analysis application

export interface FileUploadResponse {
  filename: string;
  file_id: string;
  message: string;
  analysis_summary: AnalysisSummary;
  file_detection?: FileDetection;
  processing_info?: ProcessingInfo;
}

export interface FileDetection {
  extension: string;
  size_bytes: number;
  size_mb: number;
  filename: string;
  is_supported: boolean;
  type: 'csv' | 'excel' | 'pdf';
  
  // CSV specific
  encoding?: string;
  delimiter?: string;
  estimated_columns?: number;
  sample_lines?: string[];
  
  // Excel specific
  sheet_count?: number;
  sheet_names?: string[];
  engine?: string;
  sample_columns?: string[];
  estimated_rows?: number;
  
  // PDF specific
  page_count?: number;
  is_encrypted?: boolean;
  metadata?: Record<string, any>;
  first_page_chars?: number;
  estimated_extractable?: boolean;
  sample_text?: string;
  
  error?: string;
}

export interface ProcessingInfo {
  encoding_used?: string;
  delimiter_used?: string;
  total_rows_processed?: number;
}

export interface AnalysisSummary {
  // Common fields
  shape?: [number, number];
  columns?: string[];
  dtypes?: Record<string, string>;
  null_counts?: Record<string, number>;
  null_percentages?: Record<string, number>;
  summary_stats?: Record<string, Record<string, number>>;
  charts?: Record<string, ChartData>;
  
  // Enhanced CSV/Excel fields
  column_types?: Record<string, ColumnTypeInfo>;
  data_quality?: DataQuality;
  
  // Excel specific
  total_sheets?: number;
  total_rows?: number;
  total_columns?: number;
  sheet_names?: string[];
  sheets_quality_summary?: Record<string, DataQuality>;
  overall_quality_score?: number;
  
  // PDF specific
  pages?: number;
  word_count?: number;
  char_count?: number;
  char_count_no_spaces?: number;
  paragraph_count?: number;
  sentence_count?: number;
  line_count?: number;
  non_empty_lines?: number;
  average_words_per_page?: number;
  average_chars_per_page?: number;
  longest_paragraph?: number;
  average_paragraph_length?: number;
  reading_time_minutes?: number;
  ai_summary?: string;
  metadata?: Record<string, any>;
  extraction_info?: {
    total_pages_processed: number;
    pages_with_text: number;
    extraction_success_rate: number;
  };
}

export interface ColumnTypeInfo {
  detected_type: 
    | 'integer' 
    | 'float' 
    | 'text' 
    | 'categorical' 
    | 'datetime' 
    | 'boolean'
    | 'email'
    | 'url'
    | 'phone'
    | 'currency'
    | 'percentage'
    | 'ip_address'
    | 'empty';
  confidence: number;
  pandas_dtype: string;
  null_percentage: number;
  unique_count: number;
  sample_values: any[];
  additional_info: {
    pattern_matches?: number;
    total_samples?: number;
    min_value?: number;
    max_value?: number;
    mean_value?: number;
    earliest_date?: string;
    latest_date?: string;
    boolean_values?: string[];
    categories?: Record<string, number>;
    category_count?: number;
    avg_length?: number;
    max_length?: number;
  };
}

export interface DataQuality {
  completeness_percentage: number;
  duplicate_rows: number;
  duplicate_percentage: number;
  high_null_columns: Array<{
    column: string;
    null_percentage: number;
  }>;
  data_quality_score: number;
}

export interface ChartData {
  type: 'histogram' | 'bar';
  
  // Histogram fields
  bins?: number[];
  counts?: number[];
  stats?: {
    mean: number;
    median: number;
    std: number;
  };
  
  // Bar chart fields
  categories?: string[];
  total_unique?: number;
  top_category_percentage?: number;
}

export interface ChatMessage {
  message: string;
  file_id: string;
}

export interface ChatResponse {
  response: string;
  sources: string[];
}

// Additional utility types
export interface EnhancedFileInfo {
  file_id: string;
  filename: string;
  type: string;
  processed_at?: string;
  file_size_mb?: number;
  rag_available: boolean;
  has_enhanced_analysis: boolean;
  quality_score?: number;
}

export interface FileAnalysisCapabilities {
  column_type_detection: boolean;
  data_quality_assessment: boolean;
  ai_summary: boolean;
  detailed_statistics: boolean;
}

export interface ModelInfo {
  llm_model: string;
  embedding_model: string;
  provider: string;
  model_url: string;
  api_version: string;
  supported_file_types: string[];
  capabilities: string[];
  new_features: string[];
}

export interface QualityAssessmentResponse {
  file_id: string;
  filename: string;
  data_quality: DataQuality;
  column_types: Record<string, ColumnTypeInfo>;
  recommendations: {
    high_null_columns: string;
    duplicates: string;
    data_types: string;
  };
}