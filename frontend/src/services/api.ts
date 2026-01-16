import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export interface AudioUploadResponse {
  task_id: string;
  message: string;
}

export interface ProcessStoryResponse {
  task_id: string;
  status: string;
}

export interface ProcessStatusResponse {
  task_id: string;
  status: string;
  progress: Record<string, any>;
  result?: any;
}

export interface ProcessingResult {
  task_id: string;
  status: string;
  semantic_analysis?: any;
  cocktail_mix?: any;
  presentation?: any;
  layout?: any;
  error?: string;
  progress: Record<string, any>;
}

export const uploadAudio = async (file: File): Promise<AudioUploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post<AudioUploadResponse>('/api/upload-audio', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const processStory = async (audioUrl?: string, text?: string): Promise<ProcessStoryResponse> => {
  const response = await api.post<ProcessStoryResponse>('/api/process-story', {
    audio_url: audioUrl,
    text: text,
  });
  
  return response.data;
};

export const getProcessStatus = async (taskId: string): Promise<ProcessStatusResponse> => {
  const response = await api.get<ProcessStatusResponse>(`/api/process-status/${taskId}`);
  return response.data;
};

export const getResult = async (taskId: string): Promise<ProcessingResult> => {
  const response = await api.get<ProcessingResult>(`/api/get-result/${taskId}`);
  return response.data;
};
