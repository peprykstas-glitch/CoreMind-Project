import axios from 'axios';

// Backend URL
const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

// TYPES
export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: { filename: string; content: string; score: number }[];
  latency?: number;
  query_id?: string; // NEW: For feedback tracking
  last_query?: string; // NEW: Context for feedback
}

export interface AnalyticsData {
  total: number;
  avg_latency: number;
  likes: number;
  dislikes: number;
  history: { Timestamp: string; Latency: number }[];
  models: Record<string, number>;
}

// ENDPOINTS

export const checkHealth = async () => {
  try {
    const res = await api.get('/health');
    return res.data;
  } catch (error) {
    console.error("Health Check Failed:", error);
    return null;
  }
};

export const sendMessage = async (messages: Message[], temperature: number = 0.3) => {
  const res = await api.post('/query', { 
    messages,
    temperature 
  });
  return res.data;
};

export const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const getFiles = async () => {
  const res = await api.get('/files');
  return res.data.files || [];
};

export const deleteFile = async (filename: string) => {
  const res = await api.post('/delete_file', { filename });
  return res.data;
};

// 👇 NEW FUNCTIONS (Fixes your errors)
export const sendFeedback = async (data: {
    query_id: string;
    feedback: 'positive' | 'negative';
    query: string;
    response: string;
    latency: number;
}) => {
    await api.post('/feedback', data);
};

export const getAnalytics = async (): Promise<AnalyticsData | null> => {
    try {
        const res = await api.get('/analytics');
        return res.data;
    } catch (error) {
        console.error("Analytics Error:", error);
        return null;
    }
};