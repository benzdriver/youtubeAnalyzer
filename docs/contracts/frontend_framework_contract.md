# 前端框架接口契约

**提供方**: TASK_03 (前端UI框架)  
**使用方**: TASK_09 (结果展示界面)  
**版本**: v1.0.0

## 概述

定义前端框架的接口规范，包括React组件接口、状态管理、WebSocket通信和可扩展组件架构。

## 组件接口定义

### 核心组件接口

```typescript
// 基础组件Props接口
interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  testId?: string;
}

// 分析任务组件
interface AnalysisTaskProps extends BaseComponentProps {
  taskId: string;
  onStatusChange?: (status: TaskStatus) => void;
  onComplete?: (result: AnalysisResult) => void;
  onError?: (error: AnalysisError) => void;
}

// YouTube URL输入组件
interface YouTubeInputProps extends BaseComponentProps {
  onSubmit: (url: string, options: AnalysisOptions) => void;
  isLoading?: boolean;
  disabled?: boolean;
  placeholder?: string;
  validationRules?: ValidationRule[];
}

// 进度跟踪组件
interface ProgressTrackerProps extends BaseComponentProps {
  taskId: string;
  steps: AnalysisStep[];
  currentStep?: string;
  progress: number;
  showDetails?: boolean;
  onStepClick?: (step: AnalysisStep) => void;
}

// 结果展示组件
interface ResultDisplayProps extends BaseComponentProps {
  result: AnalysisResult;
  viewMode?: 'summary' | 'detailed' | 'export';
  onExport?: (format: ExportFormat) => void;
  onShare?: (platform: SharePlatform) => void;
}
```

### 数据类型定义

```typescript
// 任务状态
enum TaskStatus {
  IDLE = 'idle',
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// 分析步骤
interface AnalysisStep {
  id: string;
  name: string;
  description: string;
  status: StepStatus;
  progress: number;
  startTime?: Date;
  endTime?: Date;
  error?: string;
}

enum StepStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  SKIPPED = 'skipped'
}

// 分析选项
interface AnalysisOptions {
  maxComments?: number;
  enableTranscription?: boolean;
  analysisDepth?: 'basic' | 'detailed' | 'comprehensive';
  language?: string;
  includeTimestamps?: boolean;
}

// 分析结果
interface AnalysisResult {
  taskId: string;
  videoInfo: VideoInfo;
  contentInsights: ContentInsights;
  commentInsights: CommentInsights;
  comprehensiveInsights: string[];
  recommendations: string[];
  createdAt: Date;
  processingTime: number;
}

// 视频信息
interface VideoInfo {
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

// 内容洞察
interface ContentInsights {
  summary: string;
  keyPoints: KeyPoint[];
  topics: string[];
  sentiment: SentimentAnalysis;
  qualityScore: number;
}

// 评论洞察
interface CommentInsights {
  totalComments: number;
  sentimentDistribution: Record<string, number>;
  topThemes: string[];
  authorEngagement: AuthorEngagement;
  communityHealth: number;
}
```

## 状态管理接口

### Zustand Store接口

```typescript
// 应用状态接口
interface AppState {
  // 当前任务
  currentTask: AnalysisTask | null;
  
  // 任务历史
  taskHistory: AnalysisTask[];
  
  // UI状态
  ui: {
    sidebarOpen: boolean;
    theme: 'light' | 'dark';
    language: string;
    notifications: Notification[];
  };
  
  // WebSocket连接状态
  websocket: {
    connected: boolean;
    reconnecting: boolean;
    lastMessage?: WebSocketMessage;
  };
  
  // 用户设置
  settings: UserSettings;
}

// 状态操作接口
interface AppActions {
  // 任务操作
  createTask: (url: string, options: AnalysisOptions) => Promise<string>;
  updateTask: (taskId: string, updates: Partial<AnalysisTask>) => void;
  deleteTask: (taskId: string) => void;
  
  // UI操作
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
  
  // WebSocket操作
  connectWebSocket: (taskId: string) => void;
  disconnectWebSocket: () => void;
  handleWebSocketMessage: (message: WebSocketMessage) => void;
  
  // 设置操作
  updateSettings: (settings: Partial<UserSettings>) => void;
}

// 完整Store接口
interface AppStore extends AppState, AppActions {}
```

### Store实现示例

```typescript
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        // 初始状态
        currentTask: null,
        taskHistory: [],
        ui: {
          sidebarOpen: true,
          theme: 'light',
          language: 'zh-CN',
          notifications: []
        },
        websocket: {
          connected: false,
          reconnecting: false
        },
        settings: {
          autoSave: true,
          notifications: true,
          defaultAnalysisDepth: 'detailed'
        },
        
        // 操作实现
        createTask: async (url: string, options: AnalysisOptions) => {
          try {
            const response = await fetch('/api/v1/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ youtube_url: url, options })
            });
            
            const result = await response.json();
            
            if (result.success) {
              const task: AnalysisTask = {
                id: result.data.task_id,
                url,
                options,
                status: TaskStatus.PENDING,
                progress: 0,
                createdAt: new Date(),
                steps: []
              };
              
              set(state => ({
                currentTask: task,
                taskHistory: [task, ...state.taskHistory]
              }));
              
              // 建立WebSocket连接
              get().connectWebSocket(task.id);
              
              return task.id;
            } else {
              throw new Error(result.error?.message || '创建任务失败');
            }
          } catch (error) {
            get().addNotification({
              id: Date.now().toString(),
              type: 'error',
              message: `任务创建失败: ${error.message}`,
              duration: 5000
            });
            throw error;
          }
        },
        
        updateTask: (taskId: string, updates: Partial<AnalysisTask>) => {
          set(state => ({
            currentTask: state.currentTask?.id === taskId 
              ? { ...state.currentTask, ...updates }
              : state.currentTask,
            taskHistory: state.taskHistory.map(task =>
              task.id === taskId ? { ...task, ...updates } : task
            )
          }));
        },
        
        connectWebSocket: (taskId: string) => {
          const ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);
          
          ws.onopen = () => {
            set(state => ({
              websocket: { ...state.websocket, connected: true, reconnecting: false }
            }));
          };
          
          ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            get().handleWebSocketMessage(message);
          };
          
          ws.onclose = () => {
            set(state => ({
              websocket: { ...state.websocket, connected: false }
            }));
          };
          
          ws.onerror = () => {
            get().addNotification({
              id: Date.now().toString(),
              type: 'error',
              message: 'WebSocket连接失败',
              duration: 3000
            });
          };
        },
        
        handleWebSocketMessage: (message: WebSocketMessage) => {
          const { type, data, task_id } = message;
          
          switch (type) {
            case 'progress_update':
              get().updateTask(task_id, {
                progress: data.progress,
                currentStep: data.current_step
              });
              break;
              
            case 'task_completed':
              get().updateTask(task_id, {
                status: TaskStatus.COMPLETED,
                progress: 100,
                result: data.result,
                completedAt: new Date()
              });
              break;
              
            case 'task_failed':
              get().updateTask(task_id, {
                status: TaskStatus.FAILED,
                error: data.error_message
              });
              break;
          }
          
          set(state => ({
            websocket: { ...state.websocket, lastMessage: message }
          }));
        }
      }),
      {
        name: 'youtube-analyzer-store',
        partialize: (state) => ({
          taskHistory: state.taskHistory,
          settings: state.settings,
          ui: { theme: state.ui.theme, language: state.ui.language }
        })
      }
    ),
    { name: 'youtube-analyzer' }
  )
);
```

## WebSocket通信接口

### WebSocket Hook

```typescript
interface UseWebSocketOptions {
  taskId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface UseWebSocketReturn {
  connected: boolean;
  reconnecting: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  
  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(`ws://localhost:8000/ws/${options.taskId}`);
      
      ws.onopen = () => {
        setConnected(true);
        setReconnecting(false);
        reconnectAttemptsRef.current = 0;
        options.onConnect?.();
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setLastMessage(message);
        options.onMessage?.(message);
      };
      
      ws.onclose = () => {
        setConnected(false);
        options.onDisconnect?.();
        
        // 自动重连
        if (reconnectAttemptsRef.current < (options.reconnectAttempts || 5)) {
          setReconnecting(true);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            connect();
          }, options.reconnectInterval || 3000);
        }
      };
      
      ws.onerror = (error) => {
        options.onError?.(error);
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('WebSocket连接失败:', error);
    }
  }, [options]);
  
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    setConnected(false);
    setReconnecting(false);
  }, []);
  
  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);
  
  return {
    connected,
    reconnecting,
    lastMessage,
    sendMessage,
    disconnect
  };
}
```

## 路由接口

### 路由配置

```typescript
// 路由定义
export const routes = {
  home: '/',
  analyze: '/analyze',
  task: '/task/:taskId',
  result: '/result/:taskId',
  history: '/history',
  settings: '/settings'
} as const;

// 路由参数类型
interface RouteParams {
  taskId?: string;
}

// 页面组件接口
interface PageProps {
  params: RouteParams;
  searchParams: Record<string, string>;
}

// 布局组件接口
interface LayoutProps {
  children: React.ReactNode;
  params: RouteParams;
}
```

## 主题和样式接口

### 主题配置

```typescript
interface ThemeConfig {
  colors: {
    primary: string;
    secondary: string;
    success: string;
    warning: string;
    error: string;
    background: string;
    surface: string;
    text: {
      primary: string;
      secondary: string;
      disabled: string;
    };
  };
  
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
  };
  
  typography: {
    fontFamily: string;
    fontSize: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
    };
    fontWeight: {
      normal: number;
      medium: number;
      bold: number;
    };
  };
  
  borderRadius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}

// 主题提供者接口
interface ThemeProviderProps {
  children: React.ReactNode;
  theme?: 'light' | 'dark';
  customTheme?: Partial<ThemeConfig>;
}
```

## 错误处理接口

### 错误边界

```typescript
interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
}

// 错误类型
interface AnalysisError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  recoverable: boolean;
}

// 错误处理Hook
interface UseErrorHandlerReturn {
  error: AnalysisError | null;
  setError: (error: AnalysisError) => void;
  clearError: () => void;
  retry: () => void;
}
```

## 性能优化接口

### 虚拟化列表

```typescript
interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  containerHeight: number;
  overscan?: number;
  onScroll?: (scrollTop: number) => void;
}

// 懒加载组件
interface LazyComponentProps {
  children: React.ReactNode;
  placeholder?: React.ReactNode;
  threshold?: number;
  rootMargin?: string;
}
```

## 测试接口

### 测试工具类型

```typescript
// 组件测试辅助
interface RenderOptions {
  initialState?: Partial<AppState>;
  theme?: 'light' | 'dark';
  locale?: string;
}

interface MockWebSocketOptions {
  autoConnect?: boolean;
  messages?: WebSocketMessage[];
  delay?: number;
}

// 测试数据工厂
interface TestDataFactory {
  createTask: (overrides?: Partial<AnalysisTask>) => AnalysisTask;
  createVideoInfo: (overrides?: Partial<VideoInfo>) => VideoInfo;
  createAnalysisResult: (overrides?: Partial<AnalysisResult>) => AnalysisResult;
  createWebSocketMessage: (type: string, data?: any) => WebSocketMessage;
}
```

## 使用示例

### 基本组件使用

```typescript
// YouTube输入组件使用
function AnalyzePage() {
  const { createTask } = useAppStore();
  
  const handleSubmit = async (url: string, options: AnalysisOptions) => {
    try {
      const taskId = await createTask(url, options);
      router.push(`/task/${taskId}`);
    } catch (error) {
      console.error('创建任务失败:', error);
    }
  };
  
  return (
    <div className="container mx-auto p-4">
      <YouTubeInput
        onSubmit={handleSubmit}
        placeholder="请输入YouTube视频链接..."
        validationRules={[
          { pattern: /youtube\.com|youtu\.be/, message: '请输入有效的YouTube链接' }
        ]}
      />
    </div>
  );
}

// 任务监控组件使用
function TaskPage({ params }: { params: { taskId: string } }) {
  const { currentTask, updateTask } = useAppStore();
  
  useWebSocket({
    taskId: params.taskId,
    onMessage: (message) => {
      if (message.type === 'progress_update') {
        updateTask(params.taskId, {
          progress: message.data.progress,
          currentStep: message.data.current_step
        });
      }
    }
  });
  
  if (!currentTask) {
    return <div>任务不存在</div>;
  }
  
  return (
    <div className="container mx-auto p-4">
      <ProgressTracker
        taskId={currentTask.id}
        steps={currentTask.steps}
        progress={currentTask.progress}
        showDetails={true}
      />
      
      {currentTask.status === TaskStatus.COMPLETED && currentTask.result && (
        <ResultDisplay
          result={currentTask.result}
          viewMode="detailed"
          onExport={(format) => console.log('导出:', format)}
        />
      )}
    </div>
  );
}
```

### 自定义Hook使用

```typescript
// 任务管理Hook
function useTaskManager() {
  const store = useAppStore();
  
  const createAndMonitorTask = useCallback(async (url: string, options: AnalysisOptions) => {
    const taskId = await store.createTask(url, options);
    
    // 设置任务完成回调
    const unsubscribe = store.subscribe(
      (state) => state.currentTask,
      (task) => {
        if (task?.id === taskId && task.status === TaskStatus.COMPLETED) {
          // 任务完成处理
          store.addNotification({
            id: Date.now().toString(),
            type: 'success',
            message: '分析完成！',
            duration: 3000
          });
          unsubscribe();
        }
      }
    );
    
    return taskId;
  }, [store]);
  
  return {
    createAndMonitorTask,
    currentTask: store.currentTask,
    taskHistory: store.taskHistory
  };
}
```
