import { AnalysisResult, ExportFormat } from '@/types/analysis';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.message || `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      errorData.code
    );
  }

  return response.json();
}

export const analysisApi = {
  async getTask(taskId: string) {
    return apiRequest(`/analysis/tasks/${taskId}`);
  },

  async getResult(taskId: string): Promise<AnalysisResult> {
    return apiRequest(`/analysis/tasks/${taskId}/result`);
  },

  async exportResult(taskId: string, format: ExportFormat) {
    const response = await fetch(`${API_BASE_URL}/analysis/tasks/${taskId}/export?format=${format}`, {
      method: 'GET',
      headers: {
        'Accept': format === 'json' ? 'application/json' : 
                 format === 'csv' ? 'text/csv' : 
                 'application/pdf'
      }
    });

    if (!response.ok) {
      throw new ApiError(
        `Export failed: ${response.statusText}`,
        response.status
      );
    }

    return response.blob();
  },

  async shareResult(taskId: string, platform: string, options: any = {}) {
    return apiRequest(`/analysis/tasks/${taskId}/share`, {
      method: 'POST',
      body: JSON.stringify({ platform, options })
    });
  }
};

export default analysisApi;
