# 系统架构概览

## 整体架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (Next.js)     │    │   (FastAPI)     │    │   Services      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • UI Components │    │ • API Gateway   │    │ • YouTube API   │
│ • State Mgmt    │◄──►│ • Task Queue    │◄──►│ • OpenAI API    │
│ • WebSocket     │    │ • WebSocket     │    │ • Whisper       │
│ • Progress UI   │    │ • Orchestrator  │    │ • yt-dlp        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Data Layer    │
                       ├─────────────────┤
                       │ • Redis (Queue) │
                       │ • PostgreSQL (Data) │
                       │ • File Storage  │
                       └─────────────────┘
```

## 技术栈选择

### 后端技术栈
- **FastAPI**: 高性能异步Web框架，自动API文档生成
- **Celery + Redis**: 分布式任务队列，支持异步处理
- **PostgreSQL**: 强大的开源对象关系数据库系统
- **WebSocket**: 实时进度推送
- **Pydantic**: 数据验证和序列化

### 前端技术栈
- **Next.js 14**: React框架，支持SSR和静态生成
- **TypeScript**: 类型安全的JavaScript
- **Tailwind CSS**: 实用优先的CSS框架
- **Zustand**: 轻量级状态管理
- **React Query**: 服务端状态管理和缓存

### 外部服务集成
- **yt-dlp**: YouTube视频下载和元数据提取
- **YouTube Data API v3**: 评论和详细信息获取
- **OpenAI Whisper**: 语音转文字
- **OpenAI GPT/Claude**: 内容分析和总结

## 模块化设计

### 后端模块结构
```
backend/
├── app/
│   ├── main.py                 # FastAPI应用入口
│   ├── api/                    # API路由
│   │   ├── v1/
│   │   │   ├── analyze.py      # 分析任务API
│   │   │   ├── tasks.py        # 任务管理API
│   │   │   └── websocket.py    # WebSocket连接
│   ├── core/                   # 核心配置
│   │   ├── config.py           # 应用配置
│   │   ├── security.py         # 安全相关
│   │   └── database.py         # 数据库连接
│   ├── services/               # 业务服务
│   │   ├── youtube_extractor.py
│   │   ├── transcription.py
│   │   ├── content_analyzer.py
│   │   ├── comment_analyzer.py
│   │   └── orchestrator.py
│   ├── models/                 # 数据模型
│   │   ├── task.py
│   │   ├── analysis.py
│   │   └── schemas.py
│   └── utils/                  # 工具函数
│       ├── file_handler.py
│       ├── validators.py
│       └── exceptions.py
├── tests/                      # 测试文件
├── requirements.txt
└── Dockerfile
```

### 前端模块结构
```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # 根布局
│   │   ├── page.tsx            # 首页
│   │   └── analyze/
│   │       └── [taskId]/
│   │           └── page.tsx    # 分析结果页
│   ├── components/             # 可复用组件
│   │   ├── ui/                 # 基础UI组件
│   │   ├── analysis/           # 分析相关组件
│   │   │   ├── AnalysisForm.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   └── ResultDisplay.tsx
│   │   └── layout/             # 布局组件
│   ├── hooks/                  # 自定义Hooks
│   │   ├── useWebSocket.ts
│   │   ├── useAnalysis.ts
│   │   └── useProgress.ts
│   ├── lib/                    # 工具库
│   │   ├── api.ts              # API客户端
│   │   ├── websocket.ts        # WebSocket客户端
│   │   └── utils.ts            # 工具函数
│   ├── store/                  # 状态管理
│   │   ├── analysisStore.ts
│   │   └── uiStore.ts
│   └── types/                  # TypeScript类型定义
│       ├── analysis.ts
│       └── api.ts
├── public/                     # 静态资源
├── package.json
└── next.config.js
```

## 插件式架构设计

### 分析器插件系统
基于 `generic-ai-agent` 的响应路由模式，设计可扩展的分析器架构：

```python
# 基于 generic-ai-agent/src/agent_core/response_router.py 的模式
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAnalyzer(ABC):
    """分析器基类，类似于 ResponseRouter 的设计模式"""
    
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.config = {}
    
    @abstractmethod
    async def analyze(self, input_data: Any) -> Any:
        """执行分析逻辑"""
        pass
    
    @abstractmethod
    def get_progress_steps(self) -> List[str]:
        """返回分析步骤列表"""
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据"""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """返回分析器元数据"""
        return {
            "name": self.name,
            "version": self.version,
            "capabilities": self.get_capabilities(),
            "estimated_time": self.estimate_processing_time()
        }

class AnalyzerRegistry:
    """分析器注册中心，类似于 ResponseRouter 的路由管理"""
    
    def __init__(self):
        self._analyzers: Dict[str, BaseAnalyzer] = {}
        self._analyzer_chains: Dict[str, List[str]] = {}
    
    def register(self, analyzer: BaseAnalyzer):
        """注册分析器"""
        self._analyzers[analyzer.name] = analyzer
    
    def get_analyzer(self, name: str) -> BaseAnalyzer:
        """获取分析器实例"""
        return self._analyzers.get(name)
    
    def create_analysis_chain(self, chain_name: str, analyzer_names: List[str]):
        """创建分析链"""
        self._analyzer_chains[chain_name] = analyzer_names
    
    def execute_chain(self, chain_name: str, input_data: Any) -> Any:
        """执行分析链"""
        chain = self._analyzer_chains.get(chain_name, [])
        result = input_data
        
        for analyzer_name in chain:
            analyzer = self.get_analyzer(analyzer_name)
            if analyzer:
                result = await analyzer.analyze(result)
        
        return result

# 具体分析器实现
class ContentAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("content_analyzer", "1.0.0")
    
    async def analyze(self, transcript_data: TranscriptData) -> ContentAnalysis:
        # 实现内容分析逻辑
        pass

class CommentAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("comment_analyzer", "1.0.0")
    
    async def analyze(self, comments_data: List[Comment]) -> CommentAnalysis:
        # 实现评论分析逻辑
        pass

class SentimentAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__("sentiment_analyzer", "1.0.0")
    
    async def analyze(self, text_data: str) -> SentimentScore:
        # 实现情感分析逻辑
        pass
```

### 配置管理系统
基于 `generic-ai-agent/src/config/env_manager.py` 的配置模式：

```python
# 参考 generic-ai-agent/src/config/env_manager.py 的设计
import os
from typing import Optional, Dict, Any
from pydantic import BaseSettings, Field

class AnalyzerConfig(BaseSettings):
    """分析器配置，类似于 EnvManager 的设计"""
    
    # YouTube API 配置
    youtube_api_key: Optional[str] = Field(None, env="YOUTUBE_API_KEY")
    youtube_quota_limit: int = Field(10000, env="YOUTUBE_QUOTA_LIMIT")
    
    # OpenAI 配置
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(4000, env="OPENAI_MAX_TOKENS")
    
    # Whisper 配置
    whisper_model: str = Field("base", env="WHISPER_MODEL")
    whisper_device: str = Field("cpu", env="WHISPER_DEVICE")
    
    # Redis 配置
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    redis_db: int = Field(0, env="REDIS_DB")
    
    # 任务配置
    max_concurrent_tasks: int = Field(5, env="MAX_CONCURRENT_TASKS")
    task_timeout: int = Field(3600, env="TASK_TIMEOUT")  # 1小时
    
    # 文件存储配置
    storage_path: str = Field("./storage", env="STORAGE_PATH")
    max_file_size: int = Field(2 * 1024 * 1024 * 1024, env="MAX_FILE_SIZE")  # 2GB
    
    class Config:
        env_file = ".env"
        case_sensitive = False

class ConfigManager:
    """配置管理器，类似于 EnvManager 的功能"""
    
    def __init__(self):
        self.config = AnalyzerConfig()
        self._analyzer_configs: Dict[str, Dict[str, Any]] = {}
    
    def get_analyzer_config(self, analyzer_name: str) -> Dict[str, Any]:
        """获取特定分析器的配置"""
        return self._analyzer_configs.get(analyzer_name, {})
    
    def set_analyzer_config(self, analyzer_name: str, config: Dict[str, Any]):
        """设置分析器配置"""
        self._analyzer_configs[analyzer_name] = config
    
    def validate_config(self) -> bool:
        """验证配置完整性"""
        required_keys = ["openai_api_key"]
        for key in required_keys:
            if not getattr(self.config, key):
                return False
        return True
```

### 前端组件扩展系统
基于 `thinkforward-devin/frontend/package.json` 的现代前端架构：

```typescript
// 分析类型配置系统
interface AnalysisTypeConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<any>;
  component: React.ComponentType<AnalysisFormProps>;
  resultComponent: React.ComponentType<ResultDisplayProps>;
  estimatedTime: number;
  features: string[];
  category: 'content' | 'social' | 'technical' | 'custom';
}

// 动态分析类型注册
class AnalysisTypeRegistry {
  private static types: Map<string, AnalysisTypeConfig> = new Map();
  
  static register(config: AnalysisTypeConfig) {
    this.types.set(config.id, config);
  }
  
  static getType(id: string): AnalysisTypeConfig | undefined {
    return this.types.get(id);
  }
  
  static getAllTypes(): AnalysisTypeConfig[] {
    return Array.from(this.types.values());
  }
  
  static getTypesByCategory(category: string): AnalysisTypeConfig[] {
    return Array.from(this.types.values())
      .filter(type => type.category === category);
  }
}

// 预定义分析类型
const analysisTypes: AnalysisTypeConfig[] = [
  {
    id: 'content',
    name: '内容分析',
    description: '分析视频内容、结构和关键信息',
    icon: FileTextIcon,
    component: ContentAnalysisForm,
    resultComponent: ContentResultDisplay,
    estimatedTime: 180,
    features: ['transcript', 'key_points', 'topics', 'sentiment'],
    category: 'content'
  },
  {
    id: 'comments',
    name: '评论分析',
    description: '分析用户评论和作者回复',
    icon: MessageSquareIcon,
    component: CommentAnalysisForm,
    resultComponent: CommentResultDisplay,
    estimatedTime: 120,
    features: ['sentiment_analysis', 'author_replies', 'themes'],
    category: 'social'
  },
  {
    id: 'comprehensive',
    name: '综合分析',
    description: '包含内容和评论的完整分析',
    icon: BarChartIcon,
    component: ComprehensiveAnalysisForm,
    resultComponent: ComprehensiveResultDisplay,
    estimatedTime: 300,
    features: ['all'],
    category: 'content'
  }
];

// 注册所有分析类型
analysisTypes.forEach(type => {
  AnalysisTypeRegistry.register(type);
});
```

## 数据流设计

### 分析流程
```
1. 用户输入YouTube链接
   ↓ [前端验证]
2. 前端验证并提交到后端
   ↓ [创建任务]
3. 后端创建分析任务并返回taskId
   ↓ [任务入队]
4. 任务进入Celery队列，开始异步处理
   ↓ [WebSocket连接]
5. 前端建立WebSocket连接监听进度
   ↓ [分析执行]
6. 各个分析模块按顺序执行:
   • YouTube数据提取 (25%)
   • 音频转录 (50%)
   • 内容分析 (75%)
   • 评论分析 (90%)
   • 结果整合 (100%)
   ↓ [实时更新]
7. 实时进度通过WebSocket推送到前端
   ↓ [完成通知]
8. 分析完成，结果存储并通知前端
   ↓ [结果展示]
9. 前端展示分析结果和导出选项
```

### 状态管理架构
```typescript
// 使用 Zustand 进行状态管理
interface AppState {
  // 分析相关状态
  analysis: {
    currentTask?: AnalysisTask;
    taskHistory: AnalysisTask[];
    isLoading: boolean;
    error?: string;
  };
  
  // UI状态
  ui: {
    activeTab: string;
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    notifications: Notification[];
  };
  
  // WebSocket状态
  websocket: {
    connected: boolean;
    reconnectAttempts: number;
    lastMessage?: WebSocketMessage;
  };
  
  // 用户偏好
  preferences: {
    defaultAnalysisType: string;
    autoExport: boolean;
    notificationSettings: NotificationSettings;
  };
}

// 状态更新动作
interface AppActions {
  // 分析动作
  startAnalysis: (input: AnalysisInput) => Promise<string>;
  updateProgress: (taskId: string, progress: number, step: string) => void;
  completeAnalysis: (taskId: string, result: AnalysisResult) => void;
  
  // UI动作
  setActiveTab: (tab: string) => void;
  toggleSidebar: () => void;
  addNotification: (notification: Notification) => void;
  
  // WebSocket动作
  connectWebSocket: (taskId: string) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
}
```

## 扩展性设计

### 插件式分析器扩展
```python
# 新分析器只需继承基类并注册
class TechnicalAnalyzer(BaseAnalyzer):
    """技术内容分析器 - 未来扩展示例"""
    
    def __init__(self):
        super().__init__("technical_analyzer", "1.0.0")
    
    async def analyze(self, transcript_data: TranscriptData) -> TechnicalAnalysis:
        # 分析技术术语、代码片段、技术概念等
        pass
    
    def get_progress_steps(self) -> List[str]:
        return [
            "提取技术术语",
            "识别代码片段", 
            "分析技术难度",
            "生成技术总结"
        ]

# 注册新分析器
registry = AnalyzerRegistry()
registry.register(TechnicalAnalyzer())

# 创建包含新分析器的分析链
registry.create_analysis_chain("technical_comprehensive", [
    "youtube_extractor",
    "transcription_service", 
    "content_analyzer",
    "technical_analyzer",  # 新增的技术分析器
    "comment_analyzer"
])
```

### 前端组件动态加载
```typescript
// 动态组件加载系统
const DynamicAnalysisForm = dynamic(() => 
  import(`@/components/analysis/${analysisType}Form`), {
  loading: () => <FormSkeleton />,
  ssr: false
});

const DynamicResultDisplay = dynamic(() =>
  import(`@/components/results/${analysisType}Display`), {
  loading: () => <ResultSkeleton />,
  ssr: false
});

// 插件式结果展示
interface ResultPlugin {
  id: string;
  name: string;
  component: React.ComponentType<ResultPluginProps>;
  supports: (resultType: string) => boolean;
}

class ResultPluginRegistry {
  private static plugins: Map<string, ResultPlugin> = new Map();
  
  static register(plugin: ResultPlugin) {
    this.plugins.set(plugin.id, plugin);
  }
  
  static getPluginsForResult(resultType: string): ResultPlugin[] {
    return Array.from(this.plugins.values())
      .filter(plugin => plugin.supports(resultType));
  }
}
```

### API扩展机制
```python
# 版本化API路由
from fastapi import APIRouter

def create_versioned_router(version: str) -> APIRouter:
    router = APIRouter(prefix=f"/api/{version}")
    
    # 动态加载版本特定的路由
    version_module = importlib.import_module(f"app.api.{version}")
    version_module.setup_routes(router)
    
    return router

# 插件式API端点
class APIPlugin:
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
    
    def register_routes(self, router: APIRouter):
        """注册插件特定的API路由"""
        pass

class APIPluginRegistry:
    def __init__(self):
        self.plugins: Dict[str, APIPlugin] = {}
    
    def register(self, plugin: APIPlugin):
        self.plugins[plugin.name] = plugin
    
    def setup_all_routes(self, router: APIRouter):
        for plugin in self.plugins.values():
            plugin.register_routes(router)
```

## 性能优化

### 后端优化策略
- **异步处理**: 使用Celery处理耗时任务，避免阻塞主线程
- **缓存策略**: Redis缓存频繁访问的数据和中间结果
- **分片处理**: 大文件分片处理，避免内存溢出
- **连接池**: 数据库和外部API连接池管理
- **任务优先级**: 基于用户等级和任务类型的优先级队列

### 前端优化策略
- **代码分割**: 按路由和组件分割代码，减少初始加载时间
- **懒加载**: 非关键组件和分析结果组件懒加载
- **状态优化**: 使用React.memo和useMemo避免不必要的重渲染
- **缓存策略**: React Query缓存API响应和分析结果
- **虚拟滚动**: 大量数据展示时使用虚拟滚动

### 数据库优化
```sql
-- 索引优化
CREATE INDEX idx_tasks_status_created ON analysis_tasks(status, created_at);
CREATE INDEX idx_tasks_user_id ON analysis_tasks(user_id);
CREATE INDEX idx_results_task_id ON analysis_results(task_id);

-- 分区策略（如果数据量大）
CREATE TABLE analysis_tasks_2024 PARTITION OF analysis_tasks
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

## 安全考虑

### 数据安全
- **输入验证**: 严格验证所有用户输入，防止注入攻击
- **文件安全**: 限制文件类型、大小和存储位置
- **API限流**: 防止API滥用和DDoS攻击
- **错误处理**: 不暴露敏感的系统信息

### 隐私保护
- **数据最小化**: 只收集分析必需的数据
- **临时存储**: 分析完成后自动清理临时文件
- **匿名化**: 不存储用户个人身份信息
- **透明度**: 明确告知数据使用方式和保留期限

### 访问控制
```python
# JWT认证中间件
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 基于角色的访问控制
class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user

# 使用示例
@router.post("/admin/tasks")
async def admin_create_task(
    task_data: TaskCreate,
    user: User = Depends(RoleChecker(["admin", "moderator"]))
):
    pass
```

## 部署架构

### 开发环境
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=sqlite:///./dev.db
    volumes:
      - ./backend:/app
      - ./storage:/app/storage
    depends_on:
      - redis
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
  
  worker:
    build: ./backend
    command: celery -A app.main worker --loglevel=info --concurrency=2
    environment:
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./storage:/app/storage
    depends_on:
      - redis

volumes:
  redis_data:
```

### 生产环境
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - backend
      - frontend
  
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/youtube_analyzer
    depends_on:
      - redis
      - postgres
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      - NEXT_PUBLIC_API_URL=https://api.youtubeanalyzer.com
      - NEXT_PUBLIC_WS_URL=wss://api.youtubeanalyzer.com
  
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=youtube_analyzer
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  worker:
    build: ./backend
    command: celery -A app.main worker --loglevel=info --concurrency=4
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - postgres

volumes:
  postgres_data:
  redis_data:
```

### 监控和日志
```python
# 集成 Prometheus 监控
from prometheus_client import Counter, Histogram, Gauge

# 指标定义
TASK_COUNTER = Counter('analysis_tasks_total', 'Total analysis tasks', ['type', 'status'])
TASK_DURATION = Histogram('analysis_task_duration_seconds', 'Task processing time')
ACTIVE_TASKS = Gauge('analysis_active_tasks', 'Currently active tasks')

# 日志配置
import logging
from pythonjsonlogger import jsonlogger

def setup_logging():
    logger = logging.getLogger()
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

## 质量保证

### 测试策略
```python
# 单元测试示例
import pytest
from app.services.content_analyzer import ContentAnalyzer

@pytest.fixture
def content_analyzer():
    return ContentAnalyzer()

@pytest.fixture
def sample_transcript():
    return TranscriptData(
        fullText="这是一个测试视频的转录内容...",
        segments=[
            TranscriptSegment(start=0, end=10, text="这是开头", confidence=0.95)
        ],
        language="zh-CN",
        confidence=0.92
    )

async def test_content_analysis(content_analyzer, sample_transcript):
    result = await content_analyzer.analyze(sample_transcript, VideoInfo())
    
    assert result is not None
    assert len(result.keyPoints) > 0
    assert result.sentiment.overall >= -1 and result.sentiment.overall <= 1

# 集成测试
@pytest.mark.asyncio
async def test_full_analysis_pipeline():
    # 测试完整的分析流程
    pass

# 性能测试
@pytest.mark.performance
async def test_analysis_performance():
    # 测试分析性能指标
    pass
```

### CI/CD流程
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install -r backend/requirements-dev.txt
      
      - name: Run tests
        run: |
          pytest backend/tests/ --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Build and push Docker images
        run: |
          docker build -t youtube-analyzer-backend ./backend
          docker build -t youtube-analyzer-frontend ./frontend
```

这个架构设计确保了系统的可扩展性、可维护性和高性能，同时为未来的功能扩展提供了坚实的基础。
