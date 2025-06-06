# API接口规范

## 核心数据模型

### AnalysisTask
```typescript
interface AnalysisTask {
  id: string;                    // 任务唯一标识
  type: AnalysisType;           // 分析类型
  status: TaskStatus;           // 任务状态
  progress: number;             // 进度百分比 (0-100)
  createdAt: string;           // 创建时间 (ISO 8601)
  updatedAt: string;           // 更新时间 (ISO 8601)
  input: AnalysisInput;        // 输入数据
  result?: AnalysisResult;     // 分析结果 (完成后)
  error?: string;              // 错误信息 (失败时)
  currentStep?: string;        // 当前执行步骤
  estimatedTimeRemaining?: number; // 预计剩余时间(秒)
}

type AnalysisType = 'content' | 'comments' | 'comprehensive' | 'custom';
type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

interface AnalysisInput {
  youtubeUrl: string;          // YouTube视频链接
  options: AnalysisOptions;    // 分析选项
}

interface AnalysisOptions {
  includeComments: boolean;    // 是否包含评论分析
  language?: string;           // 转录语言 (auto-detect if not specified)
  maxComments?: number;        // 最大评论数量 (默认: 1000)
  analysisDepth: 'basic' | 'detailed' | 'comprehensive';
  customPrompts?: CustomPrompt[]; // 自定义分析提示词
  exportFormats?: ExportFormat[]; // 导出格式
}

interface CustomPrompt {
  id: string;
  name: string;
  prompt: string;
  category: string;
}

type ExportFormat = 'json' | 'markdown' | 'pdf' | 'html';
```

### AnalysisResult
```typescript
interface AnalysisResult {
  taskId: string;
  videoInfo: VideoInfo;
  contentAnalysis: ContentAnalysis;
  commentAnalysis?: CommentAnalysis;
  summary: Summary;
  metadata: AnalysisMetadata;
}

interface VideoInfo {
  id: string;                  // YouTube视频ID
  title: string;
  description: string;
  duration: number;            // 秒数
  viewCount: number;
  likeCount: number;
  dislikeCount?: number;       // 可能不可用
  commentCount: number;
  channelId: string;
  channelName: string;
  channelSubscriberCount?: number;
  publishedAt: string;         // ISO 8601
  tags: string[];
  category: string;
  language: string;
  thumbnailUrl: string;
}

interface ContentAnalysis {
  transcript: TranscriptData;   // 转录数据
  keyPoints: KeyPoint[];       // 关键要点
  topics: Topic[];             // 主要话题
  sentiment: SentimentScore;   // 整体情感分析
  structure: ContentStructure; // 内容结构
  entities: Entity[];          // 实体识别
  keywords: Keyword[];         // 关键词
}

interface TranscriptData {
  fullText: string;            // 完整转录文本
  segments: TranscriptSegment[]; // 分段转录
  language: string;            // 检测到的语言
  confidence: number;          // 转录置信度 (0-1)
}

interface TranscriptSegment {
  start: number;               // 开始时间(秒)
  end: number;                 // 结束时间(秒)
  text: string;                // 文本内容
  confidence: number;          // 置信度
}

interface KeyPoint {
  id: string;
  text: string;
  timestamp?: number;          // 对应视频时间点
  importance: number;          // 重要性评分 (0-1)
  category: string;
}

interface Topic {
  name: string;
  relevance: number;           // 相关性评分 (0-1)
  mentions: number;            // 提及次数
  timestamps: number[];        // 相关时间点
}

interface SentimentScore {
  overall: number;             // 整体情感 (-1 to 1)
  positive: number;            // 积极情感比例
  negative: number;            // 消极情感比例
  neutral: number;             // 中性情感比例
  confidence: number;          // 置信度
}

interface ContentStructure {
  sections: ContentSection[];  // 内容分段
  outline: string[];           // 内容大纲
  type: 'educational' | 'entertainment' | 'news' | 'review' | 'tutorial' | 'other';
}

interface ContentSection {
  title: string;
  startTime: number;
  endTime: number;
  summary: string;
  keyPoints: string[];
}

interface Entity {
  text: string;
  type: 'person' | 'organization' | 'location' | 'product' | 'event' | 'other';
  confidence: number;
  mentions: number;
}

interface Keyword {
  text: string;
  frequency: number;
  relevance: number;
  category: string;
}
```

### CommentAnalysis
```typescript
interface CommentAnalysis {
  totalComments: number;
  analyzedComments: number;
  authorReplies: AuthorReply[];
  topComments: Comment[];
  sentimentDistribution: SentimentDistribution;
  commonThemes: Theme[];
  engagementMetrics: EngagementMetrics;
  timeDistribution: TimeDistribution;
}

interface Comment {
  id: string;
  text: string;
  author: string;
  authorChannelId?: string;
  likeCount: number;
  replyCount: number;
  publishedAt: string;
  sentiment: SentimentScore;
  isAuthorReply: boolean;
  parentCommentId?: string;
  relevanceScore: number;      // 与视频内容的相关性
}

interface AuthorReply {
  commentId: string;
  replyText: string;
  originalComment: string;
  publishedAt: string;
  likeCount: number;
  context: string;             // 回复的上下文分析
  sentiment: SentimentScore;
}

interface SentimentDistribution {
  positive: number;            // 积极评论比例
  negative: number;            // 消极评论比例
  neutral: number;             // 中性评论比例
  byTimeRange: TimeRangeSentiment[];
}

interface TimeRangeSentiment {
  startTime: string;
  endTime: string;
  sentiment: SentimentScore;
  commentCount: number;
}

interface Theme {
  name: string;
  frequency: number;
  sentiment: SentimentScore;
  examples: string[];          // 示例评论
  relatedKeywords: string[];
}

interface EngagementMetrics {
  averageLikes: number;
  averageReplies: number;
  topEngagedComments: Comment[];
  engagementRate: number;      // 参与度
  responseRate: number;        // 作者回复率
}

interface TimeDistribution {
  hourly: HourlyDistribution[];
  daily: DailyDistribution[];
  peakTimes: string[];
}

interface HourlyDistribution {
  hour: number;
  commentCount: number;
  averageSentiment: number;
}

interface DailyDistribution {
  date: string;
  commentCount: number;
  averageSentiment: number;
}
```

### Summary
```typescript
interface Summary {
  overview: string;            // 总体概述
  mainPoints: string[];        // 主要观点
  keyTakeaways: string[];      // 关键收获
  targetAudience: string;      // 目标受众
  contentQuality: QualityAssessment;
  recommendation: Recommendation;
  tags: string[];              // 自动生成的标签
}

interface QualityAssessment {
  score: number;               // 质量评分 (0-10)
  criteria: QualityCriteria;
  strengths: string[];
  improvements: string[];
}

interface QualityCriteria {
  clarity: number;             // 清晰度
  engagement: number;          // 参与度
  informativeness: number;     // 信息量
  production: number;          // 制作质量
  originality: number;         // 原创性
}

interface Recommendation {
  rating: number;              // 推荐评分 (0-5)
  reasoning: string;           // 推荐理由
  suitableFor: string[];       // 适合人群
  warnings?: string[];         // 注意事项
}

interface AnalysisMetadata {
  processingTime: number;      // 处理时间(秒)
  modelVersions: ModelVersions;
  costs: CostBreakdown;
  quality: QualityMetrics;
}

interface ModelVersions {
  transcription: string;       // Whisper版本
  analysis: string;            // LLM模型版本
  sentiment: string;           // 情感分析模型版本
}

interface CostBreakdown {
  transcription: number;       // 转录成本
  analysis: number;            // 分析成本
  total: number;               // 总成本
  currency: string;            // 货币单位
}

interface QualityMetrics {
  transcriptionAccuracy: number;
  analysisConfidence: number;
  completeness: number;
}
```

## REST API端点

### 1. 创建分析任务
```http
POST /api/v1/analyze
Content-Type: application/json
Authorization: Bearer {token} (可选)

{
  "youtubeUrl": "https://www.youtube.com/watch?v=VIDEO_ID",
  "type": "comprehensive",
  "options": {
    "includeComments": true,
    "language": "zh-CN",
    "maxComments": 500,
    "analysisDepth": "detailed",
    "customPrompts": [
      {
        "id": "custom_1",
        "name": "技术分析",
        "prompt": "分析视频中的技术要点和实现细节",
        "category": "technical"
      }
    ],
    "exportFormats": ["json", "markdown"]
  }
}

Response: 201 Created
{
  "taskId": "task_123456789",
  "status": "pending",
  "estimatedDuration": 300,
  "queuePosition": 2,
  "message": "任务已创建，正在队列中等待处理"
}
```

### 2. 查询任务状态
```http
GET /api/v1/tasks/{taskId}

Response: 200 OK
{
  "id": "task_123456789",
  "type": "comprehensive",
  "status": "processing",
  "progress": 45,
  "createdAt": "2024-01-01T10:00:00Z",
  "updatedAt": "2024-01-01T10:02:30Z",
  "currentStep": "content_analysis",
  "estimatedTimeRemaining": 120,
  "input": {
    "youtubeUrl": "https://www.youtube.com/watch?v=VIDEO_ID",
    "options": { /* ... */ }
  },
  "progressDetails": {
    "completed": ["video_extraction", "transcription"],
    "current": "content_analysis",
    "remaining": ["comment_analysis", "summary_generation"]
  }
}
```

### 3. 获取分析结果
```http
GET /api/v1/tasks/{taskId}/result

Response: 200 OK
{
  "taskId": "task_123456789",
  "result": {
    // AnalysisResult object
  }
}

Response: 202 Accepted (任务未完成)
{
  "message": "任务仍在处理中",
  "status": "processing",
  "progress": 75
}

Response: 404 Not Found
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "指定的任务不存在"
  }
}
```

### 4. 导出结果
```http
GET /api/v1/tasks/{taskId}/export?format=json|markdown|pdf|html

Response: 200 OK
Content-Type: application/json | text/markdown | application/pdf | text/html
Content-Disposition: attachment; filename="analysis_result.{format}"

# 对于JSON格式
{
  "taskId": "task_123456789",
  "exportedAt": "2024-01-01T10:10:00Z",
  "format": "json",
  "data": { /* AnalysisResult */ }
}
```

### 5. 取消任务
```http
DELETE /api/v1/tasks/{taskId}

Response: 200 OK
{
  "message": "任务已取消",
  "taskId": "task_123456789"
}

Response: 409 Conflict
{
  "error": {
    "code": "TASK_CANNOT_BE_CANCELLED",
    "message": "任务已完成，无法取消"
  }
}
```

### 6. 获取任务列表
```http
GET /api/v1/tasks?status=completed&limit=10&offset=0&sort=createdAt:desc

Response: 200 OK
{
  "tasks": [
    {
      "id": "task_123456789",
      "type": "comprehensive",
      "status": "completed",
      "createdAt": "2024-01-01T10:00:00Z",
      "progress": 100
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

### 7. 获取支持的分析类型
```http
GET /api/v1/analysis-types

Response: 200 OK
{
  "types": [
    {
      "id": "content",
      "name": "内容分析",
      "description": "分析视频内容、结构和关键信息",
      "estimatedTime": 180,
      "features": ["transcript", "key_points", "topics", "sentiment"]
    },
    {
      "id": "comments",
      "name": "评论分析",
      "description": "分析用户评论和作者回复",
      "estimatedTime": 120,
      "features": ["sentiment_analysis", "author_replies", "themes"]
    },
    {
      "id": "comprehensive",
      "name": "综合分析",
      "description": "包含内容和评论的完整分析",
      "estimatedTime": 300,
      "features": ["all"]
    }
  ]
}
```

## WebSocket事件

### 连接
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks/{taskId}');

// 连接认证 (可选)
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'bearer_token'
  }));
};
```

### 事件类型

#### 1. 进度更新事件
```json
{
  "type": "progress_update",
  "taskId": "task_123456789",
  "progress": 45,
  "currentStep": "content_analysis",
  "stepProgress": 75,
  "message": "正在分析视频内容结构...",
  "timestamp": "2024-01-01T10:02:30Z",
  "estimatedTimeRemaining": 120
}
```

#### 2. 步骤完成事件
```json
{
  "type": "step_completed",
  "taskId": "task_123456789",
  "completedStep": "transcription",
  "nextStep": "content_analysis",
  "progress": 50,
  "stepResult": {
    "duration": 45,
    "quality": "high",
    "language": "zh-CN"
  },
  "timestamp": "2024-01-01T10:02:00Z"
}
```

#### 3. 任务完成事件
```json
{
  "type": "task_completed",
  "taskId": "task_123456789",
  "result": {
    // AnalysisResult object
  },
  "processingTime": 285,
  "timestamp": "2024-01-01T10:05:00Z"
}
```

#### 4. 错误事件
```json
{
  "type": "task_failed",
  "taskId": "task_123456789",
  "error": {
    "code": "AUDIO_EXTRACTION_FAILED",
    "message": "无法从视频中提取音频",
    "details": {
      "videoId": "VIDEO_ID",
      "reason": "视频可能被设为私有或已删除"
    }
  },
  "timestamp": "2024-01-01T10:03:00Z"
}
```

#### 5. 警告事件
```json
{
  "type": "warning",
  "taskId": "task_123456789",
  "warning": {
    "code": "LOW_AUDIO_QUALITY",
    "message": "音频质量较低，可能影响转录准确性",
    "severity": "medium"
  },
  "timestamp": "2024-01-01T10:01:30Z"
}
```

## 内部服务接口

### YouTube数据提取服务
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class YouTubeExtractor(ABC):
    @abstractmethod
    async def extract_video_info(self, url: str) -> VideoInfo:
        """提取视频基本信息"""
        pass
    
    @abstractmethod
    async def extract_audio(self, url: str, quality: str = 'best') -> str:
        """提取音频文件，返回文件路径"""
        pass
    
    @abstractmethod
    async def extract_comments(
        self, 
        video_id: str, 
        max_count: int = 1000,
        sort_by: str = 'relevance'
    ) -> List[Comment]:
        """提取评论数据"""
        pass
    
    @abstractmethod
    async def validate_url(self, url: str) -> bool:
        """验证YouTube URL有效性"""
        pass

class YTDLPExtractor(YouTubeExtractor):
    """yt-dlp实现"""
    pass

class YouTubeAPIExtractor(YouTubeExtractor):
    """YouTube Data API实现"""
    pass
```

### 音频转录服务
```python
class TranscriptionService(ABC):
    @abstractmethod
    async def transcribe(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> TranscriptData:
        """转录音频为文本"""
        pass
    
    @abstractmethod
    async def transcribe_with_timestamps(
        self, 
        audio_path: str,
        segment_length: int = 30
    ) -> List[TranscriptSegment]:
        """带时间戳的分段转录"""
        pass
    
    @abstractmethod
    async def detect_language(self, audio_path: str) -> str:
        """检测音频语言"""
        pass

class WhisperTranscriptionService(TranscriptionService):
    """OpenAI Whisper实现"""
    pass
```

### 内容分析服务
```python
class ContentAnalyzer(ABC):
    @abstractmethod
    async def analyze_content(
        self, 
        transcript: TranscriptData, 
        video_info: VideoInfo
    ) -> ContentAnalysis:
        """分析视频内容"""
        pass
    
    @abstractmethod
    async def extract_key_points(
        self, 
        transcript: str,
        max_points: int = 10
    ) -> List[KeyPoint]:
        """提取关键要点"""
        pass
    
    @abstractmethod
    async def analyze_structure(
        self, 
        transcript: TranscriptData
    ) -> ContentStructure:
        """分析内容结构"""
        pass
    
    @abstractmethod
    async def extract_entities(self, text: str) -> List[Entity]:
        """实体识别"""
        pass

class LLMContentAnalyzer(ContentAnalyzer):
    """基于LLM的内容分析器"""
    pass
```

### 评论分析服务
```python
class CommentAnalyzer(ABC):
    @abstractmethod
    async def analyze_comments(
        self, 
        comments: List[Comment], 
        author_id: str
    ) -> CommentAnalysis:
        """分析评论数据"""
        pass
    
    @abstractmethod
    async def identify_author_replies(
        self, 
        comments: List[Comment], 
        author_id: str
    ) -> List[AuthorReply]:
        """识别作者回复"""
        pass
    
    @abstractmethod
    async def analyze_sentiment(
        self, 
        comments: List[Comment]
    ) -> SentimentDistribution:
        """情感分析"""
        pass
    
    @abstractmethod
    async def extract_themes(
        self, 
        comments: List[Comment]
    ) -> List[Theme]:
        """提取评论主题"""
        pass

class MLCommentAnalyzer(CommentAnalyzer):
    """机器学习评论分析器"""
    pass
```

### 分析编排服务
```python
class AnalysisOrchestrator:
    def __init__(
        self,
        youtube_extractor: YouTubeExtractor,
        transcription_service: TranscriptionService,
        content_analyzer: ContentAnalyzer,
        comment_analyzer: CommentAnalyzer
    ):
        self.youtube_extractor = youtube_extractor
        self.transcription_service = transcription_service
        self.content_analyzer = content_analyzer
        self.comment_analyzer = comment_analyzer
    
    async def run_analysis(
        self, 
        task: AnalysisTask,
        progress_callback: Callable[[int, str], None]
    ) -> AnalysisResult:
        """执行完整的分析流程"""
        pass
    
    async def estimate_duration(self, input_data: AnalysisInput) -> int:
        """估算分析时间"""
        pass
```

## 错误处理

### 错误代码规范
```typescript
enum ErrorCode {
  // 输入验证错误
  INVALID_URL = 'INVALID_URL',
  INVALID_PARAMETERS = 'INVALID_PARAMETERS',
  
  // 资源错误
  VIDEO_NOT_FOUND = 'VIDEO_NOT_FOUND',
  VIDEO_PRIVATE = 'VIDEO_PRIVATE',
  VIDEO_UNAVAILABLE = 'VIDEO_UNAVAILABLE',
  
  // 处理错误
  AUDIO_EXTRACTION_FAILED = 'AUDIO_EXTRACTION_FAILED',
  TRANSCRIPTION_FAILED = 'TRANSCRIPTION_FAILED',
  ANALYSIS_FAILED = 'ANALYSIS_FAILED',
  COMMENT_EXTRACTION_FAILED = 'COMMENT_EXTRACTION_FAILED',
  
  // 系统错误
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  QUOTA_EXCEEDED = 'QUOTA_EXCEEDED',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  
  // 任务错误
  TASK_NOT_FOUND = 'TASK_NOT_FOUND',
  TASK_CANCELLED = 'TASK_CANCELLED',
  TASK_TIMEOUT = 'TASK_TIMEOUT'
}

interface ErrorResponse {
  error: {
    code: ErrorCode;
    message: string;
    details?: any;
    suggestions?: string[];
  };
  timestamp: string;
  requestId: string;
  taskId?: string;
}
```

### 错误处理策略
```typescript
interface RetryConfig {
  maxAttempts: number;
  backoffMultiplier: number;
  maxBackoffTime: number;
  retryableErrors: ErrorCode[];
}

interface CircuitBreakerConfig {
  failureThreshold: number;
  recoveryTimeout: number;
  monitoringPeriod: number;
}
```

## 版本控制和兼容性

### API版本控制
- API版本通过URL路径指定: `/api/v1/`, `/api/v2/`
- 向后兼容性保证: 同一主版本内不会有破坏性变更
- 新功能通过可选字段添加
- 废弃功能会提前通知并保持至少一个版本的兼容性

### 数据模型版本控制
```typescript
interface VersionedData {
  version: string;
  data: any;
  migrationPath?: string[];
}
```

### 客户端兼容性
- 客户端应该忽略未知字段
- 新的枚举值应该有默认处理逻辑
- API响应包含版本信息用于客户端适配

## 性能和限制

### 速率限制
```http
# 响应头
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200

# 超出限制时
HTTP 429 Too Many Requests
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超出限制",
    "details": {
      "limit": 100,
      "window": "1h",
      "retryAfter": 3600
    }
  }
}
```

### 资源限制
- 最大视频时长: 4小时
- 最大评论数量: 10,000条
- 最大并发任务: 10个/用户
- 文件大小限制: 2GB

### 缓存策略
- 视频信息缓存: 24小时
- 转录结果缓存: 7天
- 分析结果缓存: 30天
- 评论数据缓存: 1小时
