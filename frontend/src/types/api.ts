import { AnalysisTask, AnalysisResult, AnalysisInput, AnalysisOptions } from './analysis';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: ApiError;
  message?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export interface CreateTaskRequest {
  youtube_url: string;
  options: AnalysisOptions;
}

export interface CreateTaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface GetTaskResponse {
  task: AnalysisTask;
}

export interface GetTasksResponse {
  tasks: AnalysisTask[];
  total: number;
  page: number;
  limit: number;
}

export interface GetResultResponse {
  result: AnalysisResult;
}

export interface ExportRequest {
  task_id: string;
  format: 'json' | 'csv' | 'pdf';
  options?: {
    include_raw_data?: boolean;
    language?: string;
  };
}

export interface ExportResponse {
  download_url: string;
  expires_at: string;
}

export interface WebSocketMessage {
  type: 'progress_update' | 'task_completed' | 'task_failed' | 'connection_established' | 'error';
  task_id: string;
  data: any;
  timestamp: string;
}

export interface ProgressUpdateData {
  progress: number;
  current_step: string;
  step_details?: string;
  estimated_time_remaining?: number;
}

export interface TaskCompletedData {
  result: AnalysisResult;
  processing_time: number;
}

export interface TaskFailedData {
  error_message: string;
  error_code: string;
  recoverable: boolean;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface FilterParams {
  status?: string[];
  type?: string[];
  date_from?: string;
  date_to?: string;
}

export interface SearchParams extends PaginationParams, FilterParams {
  query?: string;
}
