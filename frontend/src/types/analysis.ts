export enum TaskStatus {
  IDLE = 'idle',
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum StepStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SKIPPED = 'skipped'
}

export enum AnalysisType {
  COMPREHENSIVE = 'comprehensive',
  CONTENT_ONLY = 'content_only',
  COMMENTS_ONLY = 'comments_only'
}

export interface AnalysisStep {
  id: string;
  name: string;
  description: string;
  status: StepStatus;
  progress: number;
  startTime?: Date;
  endTime?: Date;
  error?: string;
}

export interface AnalysisOptions {
  maxComments?: number;
  enableTranscription?: boolean;
  analysisDepth?: 'basic' | 'detailed' | 'comprehensive';
  language?: string;
  includeTimestamps?: boolean;
}

export interface AnalysisInput {
  youtube_url: string;
  options: AnalysisOptions;
}

export interface VideoInfo {
  id: string;
  title: string;
  description?: string;
  duration: number;
  channelTitle: string;
  viewCount?: number;
  likeCount?: number;
  commentCount?: number;
  thumbnailUrl?: string;
}

export interface KeyPoint {
  timestamp: number;
  content: string;
  importance: number;
}

export interface SentimentAnalysis {
  overall: 'positive' | 'negative' | 'neutral';
  score: number;
  confidence: number;
}

export interface ContentInsights {
  summary: string;
  keyPoints: KeyPoint[];
  topics: string[];
  sentiment: SentimentAnalysis;
  qualityScore: number;
}

export interface AuthorEngagement {
  totalReplies: number;
  averageResponseTime: number;
  engagementRate: number;
}

export interface CommentInsights {
  totalComments: number;
  sentimentDistribution: Record<string, number>;
  topThemes: string[];
  authorEngagement: AuthorEngagement;
  communityHealth: number;
}

export interface AnalysisResult {
  taskId: string;
  videoInfo: VideoInfo;
  contentInsights: ContentInsights;
  commentInsights: CommentInsights;
  comprehensiveInsights: string[];
  recommendations: string[];
  createdAt: Date;
  processingTime: number;
}

export interface AnalysisTask {
  id: string;
  type: AnalysisType;
  status: TaskStatus;
  progress: number;
  createdAt: string;
  updatedAt: string;
  input: AnalysisInput;
  result?: AnalysisResult;
  error?: string;
  currentStep?: string;
  estimatedTimeRemaining?: number;
  steps: AnalysisStep[];
  url: string;
  options: AnalysisOptions;
  completedAt?: Date;
}

export interface AnalysisError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  recoverable: boolean;
}

export interface ValidationRule {
  pattern: RegExp;
  message: string;
}

export type ExportFormat = 'json' | 'csv' | 'pdf' | 'txt';
export type SharePlatform = 'twitter' | 'linkedin' | 'email' | 'copy';
