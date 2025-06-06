# 编码规范和开发指南

## 概述

本文档定义了YouTube分析工具项目的编码规范、开发流程和质量标准。所有开发者必须遵循这些规范以确保代码质量、可维护性和团队协作效率。

## 后端编码规范

### Python代码规范

#### 基础规范
- **Python版本**: 使用Python 3.11+
- **代码格式**: 使用Black进行代码格式化
- **导入排序**: 使用isort进行导入语句排序
- **类型注解**: 所有函数和方法必须包含类型注解
- **文档字符串**: 使用Google风格的docstring

```python
# 正确的函数定义示例
async def analyze_video_content(
    transcript: TranscriptData,
    video_info: VideoInfo,
    options: AnalysisOptions
) -> ContentAnalysis:
    """分析视频内容并提取关键信息.
    
    Args:
        transcript: 视频转录数据
        video_info: 视频基本信息
        options: 分析选项配置
        
    Returns:
        ContentAnalysis: 内容分析结果
        
    Raises:
        AnalysisError: 当分析过程失败时抛出
        ValidationError: 当输入数据无效时抛出
    """
    pass
```

#### 配置管理模式
基于 `generic-ai-agent/src/config/env_manager.py` 的配置管理模式：

```python
# 参考 generic-ai-agent/src/config/env_manager.py 第103-123行的模式
from pydantic import BaseSettings, Field
from typing import Optional, Dict, Any

class ServiceConfig(BaseSettings):
    """服务配置基类，遵循环境变量管理模式"""
    
    # 基础配置
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # 数据库配置
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    
    # 外部服务配置
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    youtube_api_key: Optional[str] = Field(None, env="YOUTUBE_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
    def validate_required_keys(self) -> bool:
        """验证必需的配置项"""
        required = ["openai_api_key"]
        for key in required:
            if not getattr(self, key):
                raise ValueError(f"Missing required config: {key}")
        return True

# 配置管理器单例模式
class ConfigManager:
    _instance = None
    _config = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def config(self) -> ServiceConfig:
        if self._config is None:
            self._config = ServiceConfig()
            self._config.validate_required_keys()
        return self._config
```

#### 错误处理规范
```python
# 自定义异常类
class YouTubeAnalyzerError(Exception):
    """基础异常类"""
    pass

class ValidationError(YouTubeAnalyzerError):
    """数据验证错误"""
    pass

class ExternalServiceError(YouTubeAnalyzerError):
    """外部服务调用错误"""
    pass

class AnalysisError(YouTubeAnalyzerError):
    """分析处理错误"""
    pass

# 错误处理装饰器
from functools import wraps
import logging

def handle_service_errors(func):
    """服务层错误处理装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValidationError:
            raise  # 重新抛出验证错误
        except ExternalServiceError as e:
            logging.error(f"External service error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            raise AnalysisError(f"Internal error: {str(e)}")
    return wrapper
```

#### 日志记录规范
```python
import logging
from pythonjsonlogger import jsonlogger

# 日志配置
def setup_logging(log_level: str = "INFO"):
    """配置结构化日志"""
    logger = logging.getLogger()
    
    # 清除现有处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 创建JSON格式处理器
    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, log_level.upper()))

# 日志使用示例
logger = logging.getLogger(__name__)

async def process_video(video_url: str):
    logger.info("Starting video processing", extra={
        "video_url": video_url,
        "operation": "process_video"
    })
    
    try:
        # 处理逻辑
        result = await analyze_video(video_url)
        logger.info("Video processing completed", extra={
            "video_url": video_url,
            "result_size": len(result.content)
        })
        return result
    except Exception as e:
        logger.error("Video processing failed", extra={
            "video_url": video_url,
            "error": str(e),
            "error_type": type(e).__name__
        })
        raise
```

#### 数据库操作规范
```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from contextlib import asynccontextmanager

# 数据库会话管理
@asynccontextmanager
async def get_db_session():
    """数据库会话上下文管理器"""
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# 仓储模式
class TaskRepository:
    """任务数据访问层"""
    
    async def create_task(self, task_data: TaskCreate) -> AnalysisTask:
        """创建新任务"""
        async with get_db_session() as session:
            task = AnalysisTask(**task_data.dict())
            session.add(task)
            await session.flush()
            await session.refresh(task)
            return task
    
    async def get_task_by_id(self, task_id: str) -> Optional[AnalysisTask]:
        """根据ID获取任务"""
        async with get_db_session() as session:
            result = await session.execute(
                select(AnalysisTask).where(AnalysisTask.id == task_id)
            )
            return result.scalar_one_or_none()
    
    async def update_task_progress(self, task_id: str, progress: int, status: str):
        """更新任务进度"""
        async with get_db_session() as session:
            await session.execute(
                update(AnalysisTask)
                .where(AnalysisTask.id == task_id)
                .values(progress=progress, status=status, updated_at=datetime.utcnow())
            )
```

### FastAPI应用结构规范
```python
# app/main.py - 应用入口
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import time

app = FastAPI(
    title="YouTube Analyzer API",
    description="YouTube视频内容分析API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info("Request processed", extra={
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time": process_time
    })
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 路由注册
from app.api.v1 import analyze, tasks, websocket

app.include_router(analyze.router, prefix="/api/v1", tags=["analysis"])
app.include_router(tasks.router, prefix="/api/v1", tags=["tasks"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
```

## 前端编码规范

### TypeScript代码规范

#### 基础规范
基于 `thinkforward-devin/frontend/package.json` 的依赖管理模式：

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "tailwindcss": "^3.3.0",
    "zustand": "^4.4.0",
    "@tanstack/react-query": "^5.0.0",
    "zod": "^3.22.0"
  },
  "devDependencies": {
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "prettier": "^3.0.0",
    "prettier-plugin-tailwindcss": "^0.5.0"
  }
}
```

#### 组件开发规范
```typescript
// 组件类型定义
interface AnalysisFormProps {
  onSubmit: (data: AnalysisInput) => Promise<void>;
  isLoading?: boolean;
  initialValues?: Partial<AnalysisInput>;
  className?: string;
}

// 组件实现
import { useState, useCallback } from 'react';
import { z } from 'zod';

// 数据验证schema
const analysisInputSchema = z.object({
  youtubeUrl: z.string().url('请输入有效的YouTube链接'),
  type: z.enum(['content', 'comments', 'comprehensive']),
  options: z.object({
    includeComments: z.boolean(),
    language: z.string().optional(),
    maxComments: z.number().min(1).max(10000).optional(),
    analysisDepth: z.enum(['basic', 'detailed', 'comprehensive'])
  })
});

export const AnalysisForm: React.FC<AnalysisFormProps> = ({
  onSubmit,
  isLoading = false,
  initialValues,
  className
}) => {
  const [formData, setFormData] = useState<AnalysisInput>({
    youtubeUrl: '',
    type: 'comprehensive',
    options: {
      includeComments: true,
      analysisDepth: 'detailed'
    },
    ...initialValues
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // 数据验证
      const validatedData = analysisInputSchema.parse(formData);
      setErrors({});
      
      // 提交数据
      await onSubmit(validatedData);
    } catch (error) {
      if (error instanceof z.ZodError) {
        const fieldErrors: Record<string, string> = {};
        error.errors.forEach(err => {
          const path = err.path.join('.');
          fieldErrors[path] = err.message;
        });
        setErrors(fieldErrors);
      }
    }
  }, [formData, onSubmit]);

  return (
    <form onSubmit={handleSubmit} className={className}>
      {/* 表单内容 */}
    </form>
  );
};

// 默认导出
export default AnalysisForm;
```

#### 状态管理规范
```typescript
// store/analysisStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface AnalysisState {
  // 状态定义
  currentTask?: AnalysisTask;
  taskHistory: AnalysisTask[];
  isLoading: boolean;
  error?: string;
  
  // 动作定义
  startAnalysis: (input: AnalysisInput) => Promise<string>;
  updateProgress: (taskId: string, progress: number) => void;
  completeAnalysis: (taskId: string, result: AnalysisResult) => void;
  clearError: () => void;
  reset: () => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  devtools(
    persist(
      (set, get) => ({
        // 初始状态
        taskHistory: [],
        isLoading: false,
        
        // 动作实现
        startAnalysis: async (input: AnalysisInput) => {
          set({ isLoading: true, error: undefined });
          
          try {
            const response = await fetch('/api/v1/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(input)
            });
            
            if (!response.ok) {
              throw new Error('分析请求失败');
            }
            
            const { taskId } = await response.json();
            
            // 创建任务对象
            const task: AnalysisTask = {
              id: taskId,
              type: input.type,
              status: 'pending',
              progress: 0,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              input
            };
            
            set(state => ({
              currentTask: task,
              taskHistory: [task, ...state.taskHistory],
              isLoading: false
            }));
            
            return taskId;
          } catch (error) {
            set({ 
              isLoading: false, 
              error: error instanceof Error ? error.message : '未知错误' 
            });
            throw error;
          }
        },
        
        updateProgress: (taskId: string, progress: number) => {
          set(state => {
            if (state.currentTask?.id === taskId) {
              return {
                currentTask: {
                  ...state.currentTask,
                  progress,
                  updatedAt: new Date().toISOString()
                }
              };
            }
            return state;
          });
        },
        
        completeAnalysis: (taskId: string, result: AnalysisResult) => {
          set(state => {
            if (state.currentTask?.id === taskId) {
              const completedTask = {
                ...state.currentTask,
                status: 'completed' as const,
                progress: 100,
                result,
                updatedAt: new Date().toISOString()
              };
              
              return {
                currentTask: completedTask,
                taskHistory: state.taskHistory.map(task => 
                  task.id === taskId ? completedTask : task
                )
              };
            }
            return state;
          });
        },
        
        clearError: () => set({ error: undefined }),
        
        reset: () => set({
          currentTask: undefined,
          isLoading: false,
          error: undefined
        })
      }),
      {
        name: 'analysis-store',
        partialize: (state) => ({ taskHistory: state.taskHistory })
      }
    ),
    { name: 'analysis-store' }
  )
);
```

#### 自定义Hook规范
```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useAnalysisStore } from '@/store/analysisStore';

interface UseWebSocketOptions {
  taskId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
}

export const useWebSocket = ({
  taskId,
  onMessage,
  onError,
  reconnectAttempts = 3
}: UseWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const { updateProgress, completeAnalysis } = useAnalysisStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/tasks/${taskId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      reconnectCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        // 处理不同类型的消息
        switch (message.type) {
          case 'progress_update':
            updateProgress(taskId, message.progress);
            break;
          case 'task_completed':
            completeAnalysis(taskId, message.result);
            break;
          case 'task_failed':
            console.error('Task failed:', message.error);
            break;
        }
        
        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      
      // 自动重连
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current++;
        setTimeout(connect, 1000 * reconnectCountRef.current);
      }
    };

    wsRef.current = ws;
  }, [taskId, onMessage, onError, reconnectAttempts, updateProgress, completeAnalysis]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN
  };
};
```

### CSS和样式规范
```typescript
// 使用Tailwind CSS类名规范
const buttonVariants = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white',
  secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900',
  danger: 'bg-red-600 hover:bg-red-700 text-white'
};

// 组件样式组合
interface ButtonProps {
  variant?: keyof typeof buttonVariants;
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  className,
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  const classes = [
    baseClasses,
    buttonVariants[variant],
    sizeClasses[size],
    className
  ].filter(Boolean).join(' ');

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
};
```

## 测试规范

### 后端测试
```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.core.database import get_db_session

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    """测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    """测试数据库会话"""
    async with get_db_session() as session:
        yield session

# tests/test_analysis.py
import pytest
from app.services.content_analyzer import ContentAnalyzer

class TestContentAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return ContentAnalyzer()

    @pytest.fixture
    def sample_transcript(self):
        return TranscriptData(
            fullText="这是一个测试视频的转录内容...",
            segments=[
                TranscriptSegment(start=0, end=10, text="这是开头", confidence=0.95)
            ],
            language="zh-CN",
            confidence=0.92
        )

    async def test_analyze_content_success(self, analyzer, sample_transcript):
        """测试内容分析成功场景"""
        video_info = VideoInfo(title="测试视频", duration=300)
        
        result = await analyzer.analyze_content(sample_transcript, video_info)
        
        assert result is not None
        assert len(result.keyPoints) > 0
        assert result.sentiment.overall >= -1 and result.sentiment.overall <= 1
        assert result.structure.type in ['educational', 'entertainment', 'news', 'review', 'tutorial', 'other']

    async def test_analyze_content_empty_transcript(self, analyzer):
        """测试空转录内容的处理"""
        empty_transcript = TranscriptData(
            fullText="",
            segments=[],
            language="zh-CN",
            confidence=0.0
        )
        
        with pytest.raises(ValidationError):
            await analyzer.analyze_content(empty_transcript, VideoInfo())

# 集成测试
@pytest.mark.integration
async def test_full_analysis_pipeline(client):
    """测试完整分析流程"""
    analysis_data = {
        "youtubeUrl": "https://www.youtube.com/watch?v=test",
        "type": "content",
        "options": {
            "includeComments": False,
            "analysisDepth": "basic"
        }
    }
    
    response = await client.post("/api/v1/analyze", json=analysis_data)
    assert response.status_code == 201
    
    task_data = response.json()
    assert "taskId" in task_data
    
    # 检查任务状态
    task_response = await client.get(f"/api/v1/tasks/{task_data['taskId']}")
    assert task_response.status_code == 200
```

### 前端测试
```typescript
// __tests__/components/AnalysisForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnalysisForm } from '@/components/analysis/AnalysisForm';

describe('AnalysisForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders form fields correctly', () => {
    render(<AnalysisForm onSubmit={mockOnSubmit} />);
    
    expect(screen.getByLabelText(/youtube.*链接/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/分析类型/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /开始分析/i })).toBeInTheDocument();
  });

  it('validates YouTube URL format', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm onSubmit={mockOnSubmit} />);
    
    const urlInput = screen.getByLabelText(/youtube.*链接/i);
    const submitButton = screen.getByRole('button', { name: /开始分析/i });
    
    await user.type(urlInput, 'invalid-url');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/请输入有效的YouTube链接/i)).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm onSubmit={mockOnSubmit} />);
    
    const urlInput = screen.getByLabelText(/youtube.*链接/i);
    const submitButton = screen.getByRole('button', { name: /开始分析/i });
    
    await user.type(urlInput, 'https://www.youtube.com/watch?v=test123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        youtubeUrl: 'https://www.youtube.com/watch?v=test123',
        type: 'comprehensive',
        options: {
          includeComments: true,
          analysisDepth: 'detailed'
        }
      });
    });
  });
});

// __tests__/hooks/useWebSocket.test.ts
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

// Mock WebSocket
global.WebSocket = jest.fn().mockImplementation(() => ({
  readyState: WebSocket.OPEN,
  close: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn()
}));

describe('useWebSocket', () => {
  it('connects to WebSocket on mount', () => {
    const { result } = renderHook(() => 
      useWebSocket({ taskId: 'test-task-id' })
    );
    
    expect(WebSocket).toHaveBeenCalledWith(
      expect.stringContaining('/ws/tasks/test-task-id')
    );
  });

  it('handles connection and disconnection', () => {
    const { result, unmount } = renderHook(() => 
      useWebSocket({ taskId: 'test-task-id' })
    );
    
    expect(result.current.isConnected).toBe(true);
    
    act(() => {
      result.current.disconnect();
    });
    
    unmount();
  });
});
```

## Git工作流规范

### 分支命名规范
```bash
# 功能分支
feature/task-{number}-{description}
feature/task-01-project-setup
feature/task-02-backend-api

# 修复分支
fix/issue-{number}-{description}
fix/issue-123-websocket-connection

# 热修复分支
hotfix/critical-{description}
hotfix/critical-security-patch

# 发布分支
release/v{version}
release/v1.0.0
```

### 提交信息规范
```bash
# 提交信息格式
<type>(<scope>): <subject>

<body>

<footer>

# 类型说明
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建过程或辅助工具的变动

# 示例
feat(analysis): add content analysis service

- Implement ContentAnalyzer class with LLM integration
- Add key points extraction functionality
- Include sentiment analysis for video content

Closes #123
```

### 代码审查规范
```markdown
# Pull Request模板
## 变更描述
简要描述本次变更的内容和目的

## 变更类型
- [ ] 新功能
- [ ] Bug修复
- [ ] 文档更新
- [ ] 代码重构
- [ ] 性能优化

## 测试
- [ ] 单元测试已通过
- [ ] 集成测试已通过
- [ ] 手动测试已完成

## 检查清单
- [ ] 代码遵循项目编码规范
- [ ] 已添加必要的测试用例
- [ ] 文档已更新
- [ ] 无安全漏洞
- [ ] 性能影响已评估

## 相关Issue
Closes #123
Related to #456
```

## 性能和安全规范

### 性能优化指南
```python
# 数据库查询优化
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# 使用预加载避免N+1查询
async def get_tasks_with_results():
    stmt = select(AnalysisTask).options(
        selectinload(AnalysisTask.result)
    )
    result = await session.execute(stmt)
    return result.scalars().all()

# 使用索引优化查询
# 在模型中定义索引
class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    
    id = Column(String, primary_key=True)
    status = Column(String, index=True)  # 添加索引
    created_at = Column(DateTime, index=True)  # 添加索引
    
    __table_args__ = (
        Index('idx_status_created', 'status', 'created_at'),  # 复合索引
    )
```

```typescript
// 前端性能优化
import { memo, useMemo, useCallback } from 'react';

// 使用React.memo避免不必要的重渲染
export const AnalysisResult = memo<AnalysisResultProps>(({ result }) => {
  // 使用useMemo缓存计算结果
  const processedData = useMemo(() => {
    return processAnalysisResult(result);
  }, [result]);

  // 使用useCallback缓存事件处理器
  const handleExport = useCallback((format: ExportFormat) => {
    exportResult(result, format);
  }, [result]);

  return (
    <div>
      {/* 组件内容 */}
    </div>
  );
});

// 代码分割和懒加载
const LazyAnalysisForm = lazy(() => import('@/components/analysis/AnalysisForm'));

export const AnalysisPage = () => {
  return (
    <Suspense fallback={<FormSkeleton />}>
      <LazyAnalysisForm />
    </Suspense>
  );
};
```

### 安全规范
```python
# 输入验证和清理
from pydantic import BaseModel, validator
import re

class AnalysisInput(BaseModel):
    youtubeUrl: str
    
    @validator('youtubeUrl')
    def validate_youtube_url(cls, v):
        youtube_pattern = r'^https?://(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w-]+$'
        if not re.match(youtube_pattern, v):
            raise ValueError('Invalid YouTube URL format')
        return v

# API限流
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/v1/analyze")
@limiter.limit("10/minute")
async def create_analysis(request: Request, analysis_input: AnalysisInput):
    # API实现
    pass

# 敏感信息处理
import os
from cryptography.fernet import Fernet

class SecretManager:
    def __init__(self):
        self.cipher = Fernet(os.environ.get('ENCRYPTION_KEY').encode())
    
    def encrypt_secret(self, secret: str) -> str:
        return self.cipher.encrypt(secret.encode()).decode()
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        return self.cipher.decrypt(encrypted_secret.encode()).decode()
```

## 文档规范

### API文档
```python
# 使用FastAPI自动生成API文档
from fastapi import FastAPI
from pydantic import BaseModel, Field

class AnalysisInput(BaseModel):
    """分析输入数据模型"""
    youtubeUrl: str = Field(..., description="YouTube视频链接", example="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    type: AnalysisType = Field(..., description="分析类型")
    options: AnalysisOptions = Field(..., description="分析选项")

@app.post("/api/v1/analyze", response_model=TaskResponse)
async def create_analysis(
    analysis_input: AnalysisInput,
    background_tasks: BackgroundTasks
):
    """
    创建新的视频分析任务
    
    - **youtubeUrl**: 要分析的YouTube视频链接
    - **type**: 分析类型 (content, comments, comprehensive)
    - **options**: 分析选项配置
    
    返回创建的任务ID和预估处理时间
    """
    pass
```

### 代码文档
```python
def analyze_video_content(
    transcript: TranscriptData,
    video_info: VideoInfo,
    options: AnalysisOptions
) -> ContentAnalysis:
    """分析视频内容并提取关键信息.
    
    该函数使用LLM对视频转录内容进行深度分析，提取关键要点、
    主题分类、情感倾向等信息。
    
    Args:
        transcript: 视频转录数据，包含完整文本和时间戳信息
        video_info: 视频基本信息，如标题、描述、时长等
        options: 分析选项，控制分析深度和特定功能
        
    Returns:
        ContentAnalysis: 包含以下字段的分析结果:
            - keyPoints: 关键要点列表
            - topics: 主题分类结果
            - sentiment: 情感分析评分
            - structure: 内容结构分析
            
    Raises:
        ValidationError: 当输入数据格式不正确时
        AnalysisError: 当分析过程中发生错误时
        ExternalServiceError: 当外部LLM服务不可用时
        
    Example:
        >>> transcript = TranscriptData(fullText="视频内容...")
        >>> video_info = VideoInfo(title="测试视频")
        >>> options = AnalysisOptions(analysisDepth="detailed")
        >>> result = analyze_video_content(transcript, video_info, options)
        >>> print(f"提取到 {len(result.keyPoints)} 个关键要点")
    """
    pass
```

## 质量保证

### 代码质量检查
```yaml
# .github/workflows/quality.yml
name: Code Quality

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install black isort flake8 mypy
          pip install -r requirements.txt
      
      - name: Run Black
        run: black --check .
      
      - name: Run isort
        run: isort --check-only .
      
      - name: Run flake8
        run: flake8 .
      
      - name: Run mypy
        run: mypy .

  frontend-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run ESLint
        run: |
          cd frontend
          npm run lint
      
      - name: Run Prettier
        run: |
          cd frontend
          npm run format:check
      
      - name: Type check
        run: |
          cd frontend
          npm run type-check
```

### 测试覆盖率要求
- 单元测试覆盖率 ≥ 80%
- 集成测试覆盖关键业务流程
- E2E测试覆盖主要用户场景

### 代码审查检查清单
- [ ] 代码符合编码规范
- [ ] 函数和类有适当的文档字符串
- [ ] 错误处理完整且合理
- [ ] 性能考虑（避免N+1查询、内存泄漏等）
- [ ] 安全考虑（输入验证、权限检查等）
- [ ] 测试用例充分且有意义
- [ ] 日志记录适当且有用
- [ ] 配置管理正确
- [ ] 依赖项合理且最新

遵循这些编码规范将确保项目代码的一致性、可维护性和高质量。所有开发者都应该熟悉并严格遵循这些规范。
