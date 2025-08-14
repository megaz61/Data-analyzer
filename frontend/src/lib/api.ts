import axios from 'axios';
import { FileUploadResponse, ChatMessage, ChatResponse, ProcessedFile } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadFile = async (file: File): Promise<FileUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const sendChatMessage = async (message: ChatMessage): Promise<ChatResponse> => {
  const response = await api.post('/chat', message);
  return response.data;
};

export const getFileInfo = async (fileId: string): Promise<ProcessedFile> => {
  const response = await api.get(`/file/${fileId}`);
  return response.data;
};