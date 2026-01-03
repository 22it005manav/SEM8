import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const videoService = {
  /**
   * Upload a video file
   */
  async uploadVideo(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(percentCompleted);
        }
      },
    });

    return response.data;
  },

  /**
   * Start video processing
   */
  async startProcessing(jobId, options = {}) {
    const response = await api.post('/process', {
      job_id: jobId,
      model_layers: options.modelLayers || '8',
      resolution: options.resolution || 512,
      use_fp16: options.useFp16 || false,
      device: options.device || null,
    });

    return response.data;
  },

  /**
   * Get processing status
   */
  async getStatus(jobId) {
    const response = await api.get(`/status/${jobId}`);
    return response.data;
  },

  /**
   * Get download info
   */
  async getDownloadInfo(jobId) {
    const response = await api.get(`/download/${jobId}/info`);
    return response.data;
  },

  /**
   * Get download URL
   */
  getDownloadUrl(jobId) {
    return `${API_BASE_URL}/download/${jobId}`;
  },

  /**
   * Delete job
   */
  async deleteJob(jobId) {
    const response = await api.delete(`/job/${jobId}`);
    return response.data;
  },

  /**
   * Health check
   */
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },
};

/**
 * WebSocket connection for real-time updates
 */
export class WebSocketService {
  constructor(jobId, onMessage) {
    const wsUrl = `ws://localhost:8000/api/ws/${jobId}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };
    
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
  }
  
  close() {
    if (this.ws) {
      this.ws.close();
    }
  }
  
  sendHeartbeat() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send('ping');
    }
  }
}
