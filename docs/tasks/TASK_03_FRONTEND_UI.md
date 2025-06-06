# Task 3: 前端UI框架

## 任务概述

构建YouTube分析工具的前端UI框架，包括Next.js项目结构、模块化组件架构、WebSocket客户端、响应式设计系统和状态管理设置。重点关注可扩展性，为未来的YouTube分析功能提供灵活的架构基础。

## 目标

- 建立Next.js 14的现代前端架构
- 实现模块化和可扩展的组件系统
- 配置WebSocket客户端进行实时通信
- 设计响应式UI组件库
- 建立状态管理和数据获取机制

## 可交付成果

### 1. Next.js项目结构

基于 <ref_file file="/home/ubuntu/repos/thinkforward-devin/frontend/package.json" /> 的现代前端架构：

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # 根布局
│   │   ├── page.tsx            # 首页
│   │   ├── globals.css         # 全局样式
│   │   └── analyze/
│   │       └── [taskId]/
│   │           ├── page.tsx    # 分析结果页
│   │           └── loading.tsx # 加载状态
│   ├── components/             # 可复用组件
│   │   ├── ui/                 # 基础UI组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Progress.tsx
│   │   │   └── index.ts
│   │   ├── analysis/           # 分析相关组件
│   │   │   ├── AnalysisForm.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   ├── ResultDisplay.tsx
│   │   │   └── AnalysisTypeSelector.tsx
│   │   └── layout/             # 布局组件
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── hooks/                  # 自定义Hooks
│   │   ├── useWebSocket.ts
│   │   ├── useAnalysis.ts
│   │   └── useProgress.ts
│   ├── lib/                    # 工具库
│   │   ├── api.ts              # API客户端
│   │   ├── websocket.ts        # WebSocket客户端
│   │   ├── utils.ts            # 工具函数
│   │   └── constants.ts        # 常量定义
│   ├── store/                  # 状态管理
│   │   ├── analysisStore.ts
│   │   ├── uiStore.ts
│   │   └── index.ts
│   └── types/                  # TypeScript类型定义
│       ├── analysis.ts
│       ├── api.ts
│       └── ui.ts
├── public/                     # 静态资源
│   ├── icons/
│   └── images/
├── package.json
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
└── .env.local.example
```

### 2. 核心组件实现

#### 主页面组件
```typescript
// src/app/page.tsx
'use client';

import { useState } from 'react';
import { AnalysisForm } from '@/components/analysis/AnalysisForm';
import { AnalysisTypeSelector } from '@/components/analysis/AnalysisTypeSelector';
import { Card } from '@/components/ui/Card';
import { useAnalysisStore } from '@/store/analysisStore';

export default function HomePage() {
  const [selectedType, setSelectedType] = useState<string>('comprehensive');
  const { startAnalysis, isLoading } = useAnalysisStore();

  const handleAnalysisSubmit = async (data: AnalysisInput) => {
    try {
      const taskId = await startAnalysis(data);
      // 导航到分析页面
      window.location.href = `/analyze/${taskId}`;
    } catch (error) {
      console.error('Failed to start analysis:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* 页面标题 */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              YouTube 视频分析工具
            </h1>
            <p className="text-lg text-gray-600">
              智能分析YouTube视频内容，提取关键信息和评论洞察
            </p>
          </div>

          {/* 分析类型选择器 */}
          <Card className="mb-6">
            <AnalysisTypeSelector
              selectedType={selectedType}
              onTypeChange={setSelectedType}
            />
          </Card>

          {/* 分析表单 */}
          <Card>
            <AnalysisForm
              analysisType={selectedType}
              onSubmit={handleAnalysisSubmit}
              isLoading={isLoading}
            />
          </Card>

          {/* 功能特性展示 */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              icon="🎥"
              title="内容分析"
              description="深度分析视频内容，提取关键要点和主题"
            />
            <FeatureCard
              icon="💬"
              title="评论分析"
              description="分析用户评论情感，识别作者回复"
            />
            <FeatureCard
              icon="📊"
              title="综合报告"
              description="生成完整的分析报告和可视化图表"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

const FeatureCard = ({ icon, title, description }: {
  icon: string;
  title: string;
  description: string;
}) => (
  <Card className="text-center p-6">
    <div className="text-4xl mb-4">{icon}</div>
    <h3 className="text-xl font-semibold mb-2">{title}</h3>
    <p className="text-gray-600">{description}</p>
  </Card>
);
```

#### 可扩展的分析类型选择器
```typescript
// src/components/analysis/AnalysisTypeSelector.tsx
'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface AnalysisType {
  id: string;
  name: string;
  description: string;
  icon: string;
  features: string[];
  estimatedTime: number;
  category: 'content' | 'social' | 'comprehensive' | 'custom';
}

const analysisTypes: AnalysisType[] = [
  {
    id: 'content',
    name: '内容分析',
    description: '分析视频内容、结构和关键信息',
    icon: '📝',
    features: ['转录文本', '关键要点', '主题分类', '情感分析'],
    estimatedTime: 180,
    category: 'content'
  },
  {
    id: 'comments',
    name: '评论分析',
    description: '分析用户评论和作者回复',
    icon: '💬',
    features: ['评论情感', '作者回复', '热门评论', '主题提取'],
    estimatedTime: 120,
    category: 'social'
  },
  {
    id: 'comprehensive',
    name: '综合分析',
    description: '包含内容和评论的完整分析',
    icon: '🔍',
    features: ['全部功能', '深度洞察', '完整报告', '数据导出'],
    estimatedTime: 300,
    category: 'comprehensive'
  }
];

interface AnalysisTypeSelectorProps {
  selectedType: string;
  onTypeChange: (type: string) => void;
  className?: string;
}

export const AnalysisTypeSelector: React.FC<AnalysisTypeSelectorProps> = ({
  selectedType,
  onTypeChange,
  className
}) => {
  const [expandedType, setExpandedType] = useState<string | null>(null);

  return (
    <div className={className}>
      <h2 className="text-2xl font-semibold mb-4">选择分析类型</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {analysisTypes.map((type) => (
          <Card
            key={type.id}
            className={`cursor-pointer transition-all duration-200 ${
              selectedType === type.id
                ? 'ring-2 ring-blue-500 bg-blue-50'
                : 'hover:shadow-md'
            }`}
            onClick={() => onTypeChange(type.id)}
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{type.icon}</span>
                  <h3 className="font-semibold text-lg">{type.name}</h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedType(
                      expandedType === type.id ? null : type.id
                    );
                  }}
                >
                  {expandedType === type.id ? '收起' : '详情'}
                </Button>
              </div>
              
              <p className="text-gray-600 text-sm mb-3">{type.description}</p>
              
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>预计时间: {Math.floor(type.estimatedTime / 60)}分钟</span>
                <span className="px-2 py-1 bg-gray-100 rounded-full text-xs">
                  {type.category}
                </span>
              </div>
              
              {expandedType === type.id && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="font-medium mb-2">功能特性:</h4>
                  <ul className="space-y-1">
                    {type.features.map((feature, index) => (
                      <li key={index} className="flex items-center text-sm">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
      
      {/* 自定义分析类型提示 */}
      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-center space-x-2">
          <span className="text-yellow-600">💡</span>
          <span className="text-sm text-yellow-800">
            未来版本将支持自定义分析类型和插件扩展
          </span>
        </div>
      </div>
    </div>
  );
};
```

#### 分析表单组件
```typescript
// src/components/analysis/AnalysisForm.tsx
'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card } from '@/components/ui/Card';

const analysisSchema = z.object({
  youtubeUrl: z.string().url('请输入有效的YouTube链接').refine(
    (url) => /^https?:\/\/(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[\w-]+/.test(url),
    '请输入有效的YouTube视频链接'
  ),
  includeComments: z.boolean().default(true),
  language: z.string().optional(),
  maxComments: z.number().min(1).max(10000).default(1000),
  analysisDepth: z.enum(['basic', 'detailed', 'comprehensive']).default('detailed'),
  customPrompts: z.array(z.object({
    name: z.string(),
    prompt: z.string(),
    category: z.string()
  })).optional()
});

type AnalysisFormData = z.infer<typeof analysisSchema>;

interface AnalysisFormProps {
  analysisType: string;
  onSubmit: (data: AnalysisFormData & { type: string }) => Promise<void>;
  isLoading?: boolean;
  className?: string;
}

export const AnalysisForm: React.FC<AnalysisFormProps> = ({
  analysisType,
  onSubmit,
  isLoading = false,
  className
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    setValue
  } = useForm<AnalysisFormData>({
    resolver: zodResolver(analysisSchema),
    defaultValues: {
      includeComments: true,
      maxComments: 1000,
      analysisDepth: 'detailed'
    }
  });

  const includeComments = watch('includeComments');

  const onFormSubmit = async (data: AnalysisFormData) => {
    await onSubmit({ ...data, type: analysisType });
  };

  return (
    <Card className={className}>
      <div className="p-6">
        <h2 className="text-2xl font-semibold mb-6">开始分析</h2>
        
        <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
          {/* YouTube链接输入 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              YouTube视频链接 *
            </label>
            <Input
              {...register('youtubeUrl')}
              placeholder="https://www.youtube.com/watch?v=..."
              className="w-full"
              error={errors.youtubeUrl?.message}
            />
            <p className="mt-1 text-xs text-gray-500">
              支持 youtube.com 和 youtu.be 格式的链接
            </p>
          </div>

          {/* 基础选项 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  {...register('includeComments')}
                  className="rounded border-gray-300"
                />
                <span className="text-sm font-medium">包含评论分析</span>
              </label>
              <p className="mt-1 text-xs text-gray-500">
                分析视频评论和作者回复
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                分析深度
              </label>
              <select
                {...register('analysisDepth')}
                className="w-full rounded-md border-gray-300 shadow-sm"
              >
                <option value="basic">基础分析</option>
                <option value="detailed">详细分析</option>
                <option value="comprehensive">全面分析</option>
              </select>
            </div>
          </div>

          {/* 评论相关选项 */}
          {includeComments && (
            <div className="p-4 bg-gray-50 rounded-lg">
              <h3 className="font-medium mb-3">评论分析选项</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    最大评论数量
                  </label>
                  <Input
                    type="number"
                    {...register('maxComments', { valueAsNumber: true })}
                    min={1}
                    max={10000}
                    className="w-full"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    语言偏好
                  </label>
                  <select
                    {...register('language')}
                    className="w-full rounded-md border-gray-300 shadow-sm"
                  >
                    <option value="">自动检测</option>
                    <option value="zh-CN">中文</option>
                    <option value="en">English</option>
                    <option value="ja">日本語</option>
                    <option value="ko">한국어</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* 高级选项 */}
          <div>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="mb-4"
            >
              {showAdvanced ? '隐藏' : '显示'}高级选项
            </Button>
            
            {showAdvanced && (
              <div className="p-4 bg-blue-50 rounded-lg space-y-4">
                <h3 className="font-medium">高级配置</h3>
                
                {/* 自定义提示词 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    自定义分析提示词
                  </label>
                  <textarea
                    placeholder="输入自定义的分析要求..."
                    className="w-full h-24 rounded-md border-gray-300 shadow-sm"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    可以指定特定的分析角度或关注点
                  </p>
                </div>
                
                {/* 导出格式 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    导出格式
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {['JSON', 'Markdown', 'PDF', 'HTML'].map((format) => (
                      <label key={format} className="flex items-center space-x-1">
                        <input
                          type="checkbox"
                          defaultChecked={format === 'JSON'}
                          className="rounded border-gray-300"
                        />
                        <span className="text-sm">{format}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 提交按钮 */}
          <div className="flex justify-end space-x-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => window.location.reload()}
            >
              重置
            </Button>
            <Button
              type="submit"
              disabled={isLoading}
              className="min-w-32"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>分析中...</span>
                </div>
              ) : (
                '开始分析'
              )}
            </Button>
          </div>
        </form>
      </div>
    </Card>
  );
};
```

### 3. 状态管理系统

```typescript
// src/store/analysisStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { AnalysisTask, AnalysisResult, AnalysisInput } from '@/types/analysis';

interface AnalysisState {
  // 状态
  currentTask?: AnalysisTask;
  taskHistory: AnalysisTask[];
  isLoading: boolean;
  error?: string;
  
  // 动作
  startAnalysis: (input: AnalysisInput) => Promise<string>;
  updateProgress: (taskId: string, progress: number, step?: string) => void;
  completeAnalysis: (taskId: string, result: AnalysisResult) => void;
  setError: (error: string) => void;
  clearError: () => void;
  reset: () => void;
  
  // 任务管理
  getTaskById: (taskId: string) => AnalysisTask | undefined;
  removeTask: (taskId: string) => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  devtools(
    persist(
      (set, get) => ({
        // 初始状态
        taskHistory: [],
        isLoading: false,
        
        // 开始分析
        startAnalysis: async (input: AnalysisInput) => {
          set({ isLoading: true, error: undefined });
          
          try {
            const response = await fetch('/api/v1/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(input)
            });
            
            if (!response.ok) {
              const errorData = await response.json();
              throw new Error(errorData.error?.message || '分析请求失败');
            }
            
            const { taskId, estimatedDuration } = await response.json();
            
            const task: AnalysisTask = {
              id: taskId,
              type: input.type,
              status: 'pending',
              progress: 0,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              input,
              estimatedTimeRemaining: estimatedDuration
            };
            
            set(state => ({
              currentTask: task,
              taskHistory: [task, ...state.taskHistory.slice(0, 9)], // 保留最近10个
              isLoading: false
            }));
            
            return taskId;
          } catch (error) {
            const errorMessage = error instanceof Error ? error.message : '未知错误';
            set({ isLoading: false, error: errorMessage });
            throw error;
          }
        },
        
        // 更新进度
        updateProgress: (taskId: string, progress: number, step?: string) => {
          set(state => {
            const updatedHistory = state.taskHistory.map(task => {
              if (task.id === taskId) {
                const updatedTask = {
                  ...task,
                  progress,
                  currentStep: step || task.currentStep,
                  updatedAt: new Date().toISOString()
                };
                
                // 如果是当前任务，也更新currentTask
                if (state.currentTask?.id === taskId) {
                  return updatedTask;
                }
                return updatedTask;
              }
              return task;
            });
            
            return {
              taskHistory: updatedHistory,
              currentTask: state.currentTask?.id === taskId 
                ? updatedHistory.find(t => t.id === taskId)
                : state.currentTask
            };
          });
        },
        
        // 完成分析
        completeAnalysis: (taskId: string, result: AnalysisResult) => {
          set(state => {
            const updatedHistory = state.taskHistory.map(task => {
              if (task.id === taskId) {
                const completedTask = {
                  ...task,
                  status: 'completed' as const,
                  progress: 100,
                  result,
                  updatedAt: new Date().toISOString()
                };
                return completedTask;
              }
              return task;
            });
            
            return {
              taskHistory: updatedHistory,
              currentTask: state.currentTask?.id === taskId 
                ? updatedHistory.find(t => t.id === taskId)
                : state.currentTask
            };
          });
        },
        
        // 错误处理
        setError: (error: string) => set({ error, isLoading: false }),
        clearError: () => set({ error: undefined }),
        
        // 重置状态
        reset: () => set({
          currentTask: undefined,
          isLoading: false,
          error: undefined
        }),
        
        // 工具方法
        getTaskById: (taskId: string) => {
          return get().taskHistory.find(task => task.id === taskId);
        },
        
        removeTask: (taskId: string) => {
          set(state => ({
            taskHistory: state.taskHistory.filter(task => task.id !== taskId),
            currentTask: state.currentTask?.id === taskId ? undefined : state.currentTask
          }));
        }
      }),
      {
        name: 'analysis-store',
        partialize: (state) => ({ 
          taskHistory: state.taskHistory.slice(0, 10) // 只持久化最近10个任务
        })
      }
    ),
    { name: 'analysis-store' }
  )
);
```

### 4. WebSocket客户端

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from 'react';
import { useAnalysisStore } from '@/store/analysisStore';

interface WebSocketMessage {
  type: 'progress_update' | 'task_completed' | 'task_failed' | 'warning';
  taskId: string;
  progress?: number;
  currentStep?: string;
  message?: string;
  result?: any;
  error?: any;
  timestamp: number;
}

interface UseWebSocketOptions {
  taskId: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

export const useWebSocket = ({
  taskId,
  onMessage,
  onError,
  reconnectAttempts = 5,
  reconnectInterval = 1000
}: UseWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  
  const { updateProgress, completeAnalysis, setError } = useAnalysisStore();

  const connect = useCallback(() => {
    // 清理现有连接
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/tasks/${taskId}`;
    console.log('Connecting to WebSocket:', wsUrl);
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected for task:', taskId);
      reconnectCountRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        console.log('WebSocket message received:', message);
        
        // 处理不同类型的消息
        switch (message.type) {
          case 'progress_update':
            if (message.progress !== undefined) {
              updateProgress(taskId, message.progress, message.currentStep);
            }
            break;
            
          case 'task_completed':
            if (message.result) {
              completeAnalysis(taskId, message.result);
            }
            break;
            
          case 'task_failed':
            if (message.error) {
              setError(`分析失败: ${message.error.message || '未知错误'}`);
            }
            break;
            
          case 'warning':
            console.warn('Task warning:', message.message);
            break;
        }
        
        // 调用自定义消息处理器
        onMessage?.(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      
      // 自动重连逻辑
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current++;
        const delay = reconnectInterval * Math.pow(2, reconnectCountRef.current - 1); // 指数退避
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectCountRef.current}/${reconnectAttempts})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay);
      } else {
        console.error('Max reconnection attempts reached');
        setError('连接断开，请刷新页面重试');
      }
    };

    wsRef.current = ws;
  }, [taskId, onMessage, onError, reconnectAttempts, reconnectInterval, updateProgress, completeAnalysis, setError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounting');
      wsRef.current = null;
    }
  }, []);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    connect,
    disconnect,
    sendMessage,
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    connectionState: wsRef.current?.readyState
  };
};
```

### 5. 基础UI组件库

```typescript
// src/components/ui/Button.tsx
import { forwardRef } from 'react';
import { clsx } from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }, ref) => {
    const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
    
    const variants = {
      primary: 'bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500',
      secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900 focus:ring-gray-500',
      danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500',
      ghost: 'hover:bg-gray-100 text-gray-700 focus:ring-gray-500'
    };
    
    const sizes = {
      sm: 'px-3 py-1.5 text-sm',
      md: 'px-4 py-2 text-base',
      lg: 'px-6 py-3 text-lg'
    };

    return (
      <button
        ref={ref}
        className={clsx(
          baseClasses,
          variants[variant],
          sizes[size],
          className
        )}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && (
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin mr-2" />
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）

### 阻塞任务
- Task 9: 结果展示（需要前端框架）

## 验收标准

### 功能验收
- [ ] Next.js应用能够正常启动和运行
- [ ] 所有核心组件正确渲染
- [ ] 表单验证和提交功能正常
- [ ] WebSocket连接和实时更新正常
- [ ] 状态管理正确工作
- [ ] 响应式设计在不同设备上正常显示

### 技术验收
- [ ] 页面加载时间 < 3秒
- [ ] 组件渲染性能良好（无明显卡顿）
- [ ] TypeScript类型检查通过
- [ ] ESLint和Prettier检查通过
- [ ] 浏览器兼容性测试通过

### 质量验收
- [ ] 组件测试覆盖率 ≥ 70%
- [ ] 可访问性标准符合WCAG 2.1 AA
- [ ] 代码遵循项目编码规范
- [ ] 组件文档完整
- [ ] 设计系统一致性

## 测试要求

### 组件测试
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

  it('renders all form fields', () => {
    render(<AnalysisForm analysisType="content" onSubmit={mockOnSubmit} />);
    
    expect(screen.getByLabelText(/youtube.*链接/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/包含评论分析/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /开始分析/i })).toBeInTheDocument();
  });

  it('validates YouTube URL format', async () => {
    const user = userEvent.setup();
    render(<AnalysisForm analysisType="content" onSubmit={mockOnSubmit} />);
    
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
    render(<AnalysisForm analysisType="comprehensive" onSubmit={mockOnSubmit} />);
    
    const urlInput = screen.getByLabelText(/youtube.*链接/i);
    const submitButton = screen.getByRole('button', { name: /开始分析/i });
    
    await user.type(urlInput, 'https://www.youtube.com/watch?v=test123');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          youtubeUrl: 'https://www.youtube.com/watch?v=test123',
          type: 'comprehensive'
        })
      );
    });
  });
});
```

## 预估工作量

- **开发时间**: 4-5天
- **测试时间**: 1.5天
- **设计调优**: 1天
- **文档时间**: 0.5天
- **总计**: 7天

## 关键路径

此任务与Task 2并行执行，完成后为Task 9提供前端基础设施。

## 交付检查清单

- [ ] Next.js项目结构完整
- [ ] 所有核心组件已实现
- [ ] 状态管理系统已配置
- [ ] WebSocket客户端已实现
- [ ] 基础UI组件库已完成
- [ ] 响应式设计已实现
- [ ] 组件测试通过
- [ ] TypeScript类型检查通过
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，为后续任务提供：
- 完整的前端组件库
- 状态管理基础设施
- WebSocket实时通信能力
- 可扩展的UI架构
- 类型安全的开发环境

这些将被Task 9（结果展示）直接使用，并为未来的YouTube分析功能扩展提供基础。
