# Task 3: 前端UI框架 - Sub-Session Prompt

## 项目背景

你正在为YouTube视频分析工具构建Next.js前端界面。这个前端需要提供：
- 简洁直观的YouTube链接输入界面
- 实时分析进度显示
- 多维度分析结果展示
- 响应式设计支持
- 可扩展的组件架构

## 任务目标

建立完整的Next.js前端框架，包括页面路由、组件系统、状态管理、WebSocket通信和UI组件库。

## 具体要求

### 1. Next.js应用结构
参考 <ref_file file="/home/ubuntu/repos/thinkforward-devin/frontend/package.json" /> 的项目配置：

```typescript
// src/app/layout.tsx
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'YouTube分析工具',
  description: '智能分析YouTube视频内容和评论',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center py-4">
                <h1 className="text-2xl font-bold text-gray-900">
                  YouTube分析工具
                </h1>
                <nav className="flex space-x-4">
                  <a href="/" className="text-gray-600 hover:text-gray-900">
                    首页
                  </a>
                  <a href="/history" className="text-gray-600 hover:text-gray-900">
                    历史记录
                  </a>
                </nav>
              </div>
            </div>
          </header>
          <main>{children}</main>
        </div>
      </body>
    </html>
  )
}
```

### 2. 状态管理
使用Zustand进行状态管理，参考现代React状态管理模式：

```typescript
// src/store/analysisStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AnalysisTask {
  id: string;
  youtube_url: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  current_step?: string;
  progress: number;
  created_at: string;
  result?: any;
}

interface AnalysisStore {
  tasks: AnalysisTask[];
  currentTask: AnalysisTask | null;
  
  createTask: (url: string, options: any) => Promise<string>;
  updateTask: (taskId: string, updates: Partial<AnalysisTask>) => void;
  getTaskById: (taskId: string) => AnalysisTask | undefined;
}

export const useAnalysisStore = create<AnalysisStore>()(
  persist(
    (set, get) => ({
      tasks: [],
      currentTask: null,

      createTask: async (url: string, options: any) => {
        const response = await fetch('/api/v1/analysis/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ youtube_url: url, options }),
        });

        if (!response.ok) throw new Error('Failed to create task');
        
        const task = await response.json();
        set(state => ({
          tasks: [task, ...state.tasks],
          currentTask: task
        }));

        return task.id;
      },

      updateTask: (taskId: string, updates: Partial<AnalysisTask>) => {
        set(state => ({
          tasks: state.tasks.map(task =>
            task.id === taskId ? { ...task, ...updates } : task
          )
        }));
      },

      getTaskById: (taskId: string) => {
        return get().tasks.find(task => task.id === taskId);
      }
    }),
    { name: 'analysis-store' }
  )
);
```

### 3. WebSocket通信
实现实时进度更新：

```typescript
// src/hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';
import { useAnalysisStore } from '@/store/analysisStore';

interface UseWebSocketProps {
  taskId: string;
  onMessage?: (message: any) => void;
}

export const useWebSocket = ({ taskId, onMessage }: UseWebSocketProps) => {
  const [isConnected, setIsConnected] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const { updateTask } = useAnalysisStore();

  useEffect(() => {
    if (!taskId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${taskId}`;

    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => setIsConnected(true);
    
    ws.current.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'progress_update') {
        updateTask(taskId, {
          progress: message.progress,
          current_step: message.message,
          status: 'processing'
        });
      } else if (message.type === 'task_completed') {
        updateTask(taskId, {
          status: 'completed',
          progress: 100,
          result: message.result
        });
      }

      onMessage?.(message);
    };

    ws.current.onclose = () => setIsConnected(false);

    return () => ws.current?.close();
  }, [taskId, updateTask, onMessage]);

  return { isConnected };
};
```

### 4. 可扩展的组件架构
设计模块化组件系统，为未来功能扩展做准备：

```typescript
// src/components/analysis/AnalysisTypeSelector.tsx
'use client';

interface AnalysisType {
  id: string;
  name: string;
  description: string;
  icon: string;
  features: string[];
}

const analysisTypes: AnalysisType[] = [
  {
    id: 'comprehensive',
    name: '全面分析',
    description: '包含内容分析、评论分析和作者互动分析',
    icon: '🔍',
    features: ['音频转录', '内容分析', '评论分析', '作者回复分析']
  },
  {
    id: 'content_only',
    name: '内容分析',
    description: '仅分析视频内容，不包含评论',
    icon: '📝',
    features: ['音频转录', '关键要点提取', '主题分类']
  },
  {
    id: 'comments_only',
    name: '评论分析',
    description: '专注于评论和观众反馈分析',
    icon: '💬',
    features: ['评论情感分析', '作者回复分析', '互动质量评估']
  }
];

interface AnalysisTypeSelectorProps {
  selectedType: string;
  onTypeChange: (type: string) => void;
}

export const AnalysisTypeSelector: React.FC<AnalysisTypeSelectorProps> = ({
  selectedType,
  onTypeChange
}) => {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">选择分析类型</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {analysisTypes.map((type) => (
          <div
            key={type.id}
            className={`p-4 border rounded-lg cursor-pointer transition-colors ${
              selectedType === type.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => onTypeChange(type.id)}
          >
            <div className="text-center mb-3">
              <div className="text-3xl mb-2">{type.icon}</div>
              <h4 className="font-semibold">{type.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{type.description}</p>
            </div>
            <div className="space-y-1">
              {type.features.map((feature, index) => (
                <div key={index} className="flex items-center text-sm">
                  <span className="text-green-500 mr-2">✓</span>
                  {feature}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

## 验收标准

### 功能验收
- [ ] 页面正常渲染和导航
- [ ] YouTube URL输入和验证正常
- [ ] WebSocket实时通信正常
- [ ] 状态管理正确工作
- [ ] 响应式设计适配各种设备
- [ ] 组件复用性良好

### 技术验收
- [ ] 页面加载时间 < 3秒
- [ ] 组件渲染性能良好
- [ ] WebSocket连接稳定
- [ ] 状态持久化正常
- [ ] 错误处理完善

### 质量验收
- [ ] 组件测试覆盖率 ≥ 70%
- [ ] 可访问性标准符合WCAG 2.1 AA
- [ ] 代码遵循项目规范
- [ ] UI设计一致性
- [ ] 用户体验流畅

## 测试要求

### 组件测试
```typescript
// __tests__/components/UrlInput.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { UrlInput } from '@/components/UrlInput';

describe('UrlInput', () => {
  const mockOnSubmit = jest.fn();

  it('validates YouTube URL correctly', () => {
    render(<UrlInput onSubmit={mockOnSubmit} isLoading={false} />);
    
    const input = screen.getByPlaceholderText('粘贴YouTube视频链接...');
    fireEvent.change(input, { target: { value: 'https://youtube.com/watch?v=test' } });
    
    const button = screen.getByText('开始分析');
    fireEvent.click(button);
    
    expect(mockOnSubmit).toHaveBeenCalledWith('https://youtube.com/watch?v=test', {});
  });
});
```

## 交付物清单

- [ ] Next.js应用结构 (src/app/)
- [ ] 主页面组件 (src/app/page.tsx)
- [ ] URL输入组件 (src/components/UrlInput.tsx)
- [ ] 状态管理 (src/store/analysisStore.ts)
- [ ] WebSocket Hook (src/hooks/useWebSocket.ts)
- [ ] UI组件库 (src/components/ui/)
- [ ] 分析类型选择器 (src/components/analysis/)
- [ ] Tailwind CSS配置
- [ ] 组件测试文件
- [ ] TypeScript配置

## 关键接口

完成此任务后，需要为后续任务提供：
- 标准化的React组件接口
- WebSocket通信能力
- 状态管理系统
- 可扩展的UI架构

## 预估时间

- 开发时间: 3-4天
- 测试时间: 1天
- UI/UX优化: 1天
- 文档时间: 0.5天
- 总计: 5.5-6.5天

## 注意事项

1. 确保组件设计具有良好的可扩展性
2. WebSocket连接要处理断线重连
3. 状态管理要考虑持久化
4. UI设计要保持一致性
5. 响应式设计要适配各种设备

这是用户交互的核心界面，请确保用户体验的流畅性和直观性。
