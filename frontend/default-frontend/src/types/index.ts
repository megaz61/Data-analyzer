export interface FileUploadResponse {
  filename: string;
  file_id: string;
  message: string;
  analysis_summary: any;
}

export interface ChatMessage {
  message: string;
  file_id?: string;
}

export interface ChatResponse {
  response: string;
  sources: string[];
}

export interface ProcessedFile {
  file_id: string;
  filename: string;
  type: string;
  analysis: any;
}