// frontend/src/lib/api.ts
import axios from "axios";

export type ChatMessage = {
  file_id?: string;
  fileId?: string;
  message?: string;
  user_message?: string;
  top_k?: number;
  temperature?: number;
  top_p?: number;
  max_output_tokens?: number;
};

export type ChatResponse = {
  answer?: string;
  response?: string;
  sources?: Array<{ snippet: string; score: number } | string>;
  used_top_k?: number;
  model?: string;
};

export type FileUploadResponse = {
  file_id: string;
  filename: string;
  type: string;
  analysis_summary?: Record<string, any>;
  preview?: Record<string, any>;
  processing_info: Record<string, any>;
};

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const api = axios.create({ baseURL: BASE });

function buildChatBody(msg: ChatMessage) {
  const file_id = msg.file_id ?? msg.fileId;
  const user_message = msg.user_message ?? msg.message;
  if (!file_id) throw new Error("file_id missing");
  if (!user_message) throw new Error("message missing");
  return {
    file_id,
    user_message,
    top_k: msg.top_k ?? 3,
    temperature: msg.temperature ?? 0.2,
    top_p: msg.top_p ?? 0.9,
    max_output_tokens: msg.max_output_tokens ?? 768,
  };
}

export async function uploadFile(file: File): Promise<FileUploadResponse> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await axios.post(`${BASE}/upload`, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function sendChatMessage(msg: ChatMessage): Promise<ChatResponse> {
  const body = buildChatBody(msg);
  try {
    const r = await api.post("/chat", body);
    return r.data;
  } catch (err: any) {
    if (err?.response?.status === 404) {
      const r2 = await api.post("/api/chat", body);
      return r2.data;
    }
    throw err;
  }
}

export async function getFileInfo(fileId: string) {
  const r = await api.get(`/file/${fileId}`);
  return r.data;
}
