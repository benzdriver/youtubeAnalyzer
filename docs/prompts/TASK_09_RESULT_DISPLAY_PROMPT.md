# Task 9: 结果展示界面 - Sub-Session Prompt

## 必读文档

**重要提示**: 开始此任务前，你必须阅读并理解以下文档：

### 核心协调文档
- `docs/TASK_COORDINATION.md` - 整体任务依赖关系和项目结构
- `docs/ARCHITECTURE_OVERVIEW.md` - 系统架构和技术栈
- `docs/CODING_STANDARDS.md` - 代码格式、命名规范和最佳实践
- `docs/API_SPECIFICATIONS.md` - 完整API接口定义

### 任务专用文档
- `docs/tasks/TASK_09_RESULT_DISPLAY.md` - 详细任务要求和验收标准
- `docs/contracts/result_display_contract.md` - 结果展示接口规范

### 参考文档
- `docs/DEVELOPMENT_SETUP.md` - 开发环境配置
- `docs/PROGRESS_TRACKER.md` - 进度跟踪和任务状态更新

### 依赖关系
- Task 1 (项目配置) 必须先完成
- Task 2 (后端API) 必须先完成
- Task 3 (前端UI框架) 必须先完成
- Task 8 (分析编排器) 必须先完成
- 查看 `docs/contracts/frontend_framework_contract.md` 了解前端框架接口
- 查看 `docs/contracts/orchestrator_contract.md` 了解编排器接口

## 项目背景

你正在为YouTube视频分析工具构建结果展示界面。这个界面需要：
- 实时显示分析进度
- 展示多维度分析结果
- 提供直观的数据可视化
- 支持结果导出和分享
- 确保良好的用户体验

## 任务目标

实现完整的结果展示系统，包括进度跟踪、结果展示、数据可视化、导出功能和响应式设计。

## 具体要求

### 1. 分析结果页面组件

```typescript
// src/app/analyze/[taskId]/page.tsx
'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card } from '@/components/ui/Card';
import { ProgressTracker } from '@/components/analysis/ProgressTracker';
import { ResultDisplay } from '@/components/analysis/ResultDisplay';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useAnalysisStore } from '@/store/analysisStore';

export default function AnalysisPage() {
  const params = useParams();
  const taskId = params.taskId as string;
  const { getTaskById, updateTask } = useAnalysisStore();
  const [task, setTask] = useState(getTaskById(taskId));

  // WebSocket连接用于实时更新
  const { isConnected } = useWebSocket({
    taskId,
    onMessage: (message) => {
      if (message.type === 'progress_update') {
        updateTask(taskId, {
          progress: message.progress,
          current_step: message.message
        });
        setTask(getTaskById(taskId));
      } else if (message.type === 'task_completed') {
        updateTask(taskId, {
          status: 'completed',
          result: message.result
        });
        setTask(getTaskById(taskId));
      }
    }
  });

  useEffect(() => {
    // 定期更新任务状态
    const interval = setInterval(() => {
      const updatedTask = getTaskById(taskId);
      setTask(updatedTask);
    }, 1000);

    return () => clearInterval(interval);
  }, [taskId, getTaskById]);

  if (!task) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Card className="p-8 text-center">
          <h2 className="text-xl font-semibold mb-4">任务不存在</h2>
          <p className="text-gray-600">找不到指定的分析任务</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* 页面标题 */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          视频分析结果
        </h1>
        <p className="text-gray-600">
          分析ID: {taskId}
        </p>
      </div>

      {/* 连接状态指示器 */}
      <div className="mb-6">
        <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${
          isConnected 
            ? 'bg-green-100 text-green-800' 
            : 'bg-red-100 text-red-800'
        }`}>
          <div className={`w-2 h-2 rounded-full mr-2 ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`} />
          {isConnected ? '实时连接' : '连接断开'}
        </div>
      </div>

      {/* 进度跟踪器 */}
      <ProgressTracker 
        task={task}
        className="mb-8"
      />

      {/* 结果展示 */}
      {task.status === 'completed' && task.result ? (
        <ResultDisplay 
          result={task.result}
          videoUrl={task.youtube_url}
        />
      ) : task.status === 'failed' ? (
        <Card className="p-8 text-center border-red-200">
          <div className="text-red-500 text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-red-700 mb-4">
            分析失败
          </h2>
          <p className="text-gray-600 mb-4">
            {task.current_step || '分析过程中出现错误'}
          </p>
          <button 
            onClick={() => window.location.href = '/'}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700"
          >
            重新开始
          </button>
        </Card>
      ) : (
        <Card className="p-8 text-center">
          <div className="text-blue-500 text-4xl mb-4">⏳</div>
          <h2 className="text-xl font-semibold mb-4">
            分析进行中...
          </h2>
          <p className="text-gray-600">
            请耐心等待分析完成
          </p>
        </Card>
      )}
    </div>
  );
}
```

### 2. 进度跟踪组件

```typescript
// src/components/analysis/ProgressTracker.tsx
'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';

interface ProgressStep {
  id: string;
  name: string;
  description: string;
  weight: number;
}

const analysisSteps: ProgressStep[] = [
  {
    id: 'extraction',
    name: '数据提取',
    description: '获取视频信息、音频和评论',
    weight: 25
  },
  {
    id: 'transcription',
    name: '音频转录',
    description: '将音频转换为文字',
    weight: 30
  },
  {
    id: 'content_analysis',
    name: '内容分析',
    description: '分析视频内容和主题',
    weight: 25
  },
  {
    id: 'comment_analysis',
    name: '评论分析',
    description: '分析用户评论和互动',
    weight: 15
  },
  {
    id: 'finalization',
    name: '生成报告',
    description: '整合分析结果',
    weight: 5
  }
];

interface ProgressTrackerProps {
  task: any;
  className?: string;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ 
  task, 
  className = '' 
}) => {
  const getCurrentStepIndex = () => {
    const currentStep = task.current_step?.toLowerCase() || '';
    
    if (currentStep.includes('提取') || currentStep.includes('extraction')) return 0;
    if (currentStep.includes('转录') || currentStep.includes('transcription')) return 1;
    if (currentStep.includes('内容分析') || currentStep.includes('content')) return 2;
    if (currentStep.includes('评论分析') || currentStep.includes('comment')) return 3;
    if (currentStep.includes('报告') || currentStep.includes('finalization')) return 4;
    
    return -1;
  };

  const currentStepIndex = getCurrentStepIndex();
  const progress = task.progress || 0;

  return (
    <Card className={`p-6 ${className}`}>
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-lg font-semibold">分析进度</h3>
          <span className="text-sm text-gray-500">
            {progress}% 完成
          </span>
        </div>
        
        {/* 总体进度条 */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
        
        {task.current_step && (
          <p className="text-sm text-gray-600 mt-2">
            当前步骤: {task.current_step}
          </p>
        )}
      </div>

      {/* 步骤详情 */}
      <div className="space-y-4">
        {analysisSteps.map((step, index) => {
          const isCompleted = index < currentStepIndex || task.status === 'completed';
          const isCurrent = index === currentStepIndex;
          const isPending = index > currentStepIndex && task.status !== 'completed';

          return (
            <div key={step.id} className="flex items-center space-x-4">
              {/* 步骤图标 */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                isCompleted 
                  ? 'bg-green-100 text-green-700' 
                  : isCurrent 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'bg-gray-100 text-gray-500'
              }`}>
                {isCompleted ? '✓' : index + 1}
              </div>

              {/* 步骤信息 */}
              <div className="flex-1">
                <div className={`font-medium ${
                  isCompleted 
                    ? 'text-green-700' 
                    : isCurrent 
                      ? 'text-blue-700' 
                      : 'text-gray-500'
                }`}>
                  {step.name}
                </div>
                <div className="text-sm text-gray-600">
                  {step.description}
                </div>
              </div>

              {/* 状态指示器 */}
              <div className="flex-shrink-0">
                {isCompleted && (
                  <span className="text-green-600 text-sm">已完成</span>
                )}
                {isCurrent && (
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-blue-600 text-sm">进行中</span>
                  </div>
                )}
                {isPending && (
                  <span className="text-gray-400 text-sm">等待中</span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* 预计完成时间 */}
      {task.status === 'processing' && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <div className="text-sm text-blue-700">
            <strong>预计完成时间:</strong> 约 {Math.max(1, Math.ceil((100 - progress) / 10))} 分钟
          </div>
        </div>
      )}
    </Card>
  );
};
```

### 3. 结果展示组件

```typescript
// src/components/analysis/ResultDisplay.tsx
'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { VideoSummary } from './VideoSummary';
import { ContentAnalysisView } from './ContentAnalysisView';
import { CommentAnalysisView } from './CommentAnalysisView';
import { ExportOptions } from './ExportOptions';

interface ResultDisplayProps {
  result: any;
  videoUrl: string;
}

type TabType = 'summary' | 'content' | 'comments' | 'export';

export const ResultDisplay: React.FC<ResultDisplayProps> = ({ 
  result, 
  videoUrl 
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('summary');

  const tabs = [
    { id: 'summary', name: '总览', icon: '📊' },
    { id: 'content', name: '内容分析', icon: '📝' },
    { id: 'comments', name: '评论分析', icon: '💬' },
    { id: 'export', name: '导出', icon: '📤' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'summary':
        return <VideoSummary result={result} videoUrl={videoUrl} />;
      case 'content':
        return <ContentAnalysisView data={result.content_insights} />;
      case 'comments':
        return <CommentAnalysisView data={result.comment_insights} />;
      case 'export':
        return <ExportOptions result={result} videoUrl={videoUrl} />;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* 标签导航 */}
      <Card className="p-1">
        <div className="flex space-x-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-md text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.name}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* 标签内容 */}
      <div className="min-h-[600px]">
        {renderTabContent()}
      </div>
    </div>
  );
};
```

### 4. 视频总览组件

```typescript
// src/components/analysis/VideoSummary.tsx
'use client';

import React from 'react';
import { Card } from '@/components/ui/Card';

interface VideoSummaryProps {
  result: any;
  videoUrl: string;
}

export const VideoSummary: React.FC<VideoSummaryProps> = ({ 
  result, 
  videoUrl 
}) => {
  const summary = result.summary || {};
  const contentInsights = result.content_insights || {};
  const commentInsights = result.comment_insights || {};

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  return (
    <div className="space-y-6">
      {/* 视频基本信息 */}
      <Card className="p-6">
        <div className="flex items-start space-x-4">
          {summary.thumbnail_url && (
            <img 
              src={summary.thumbnail_url} 
              alt="视频缩略图"
              className="w-32 h-24 object-cover rounded-lg"
            />
          )}
          <div className="flex-1">
            <h2 className="text-xl font-bold text-gray-900 mb-2">
              {summary.video_title || '未知标题'}
            </h2>
            <p className="text-gray-600 mb-4">
              {summary.channel_title || '未知频道'}
            </p>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-500">时长:</span>
                <div className="font-medium">
                  {summary.duration ? formatDuration(summary.duration) : 'N/A'}
                </div>
              </div>
              <div>
                <span className="text-gray-500">观看次数:</span>
                <div className="font-medium">
                  {summary.view_count ? formatNumber(summary.view_count) : 'N/A'}
                </div>
              </div>
              <div>
                <span className="text-gray-500">点赞数:</span>
                <div className="font-medium">
                  {summary.like_count ? formatNumber(summary.like_count) : 'N/A'}
                </div>
              </div>
              <div>
                <span className="text-gray-500">上传时间:</span>
                <div className="font-medium">
                  {summary.upload_date ? new Date(summary.upload_date).toLocaleDateString() : 'N/A'}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* 分析摘要 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 内容分析摘要 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <span className="mr-2">📝</span>
            内容分析摘要
          </h3>
          
          {contentInsights.summary ? (
            <p className="text-gray-700 leading-relaxed mb-4">
              {contentInsights.summary}
            </p>
          ) : (
            <p className="text-gray-500">暂无内容分析数据</p>
          )}

          {contentInsights.topic_analysis && (
            <div className="space-y-2">
              <div>
                <span className="text-sm text-gray-500">主要主题:</span>
                <div className="font-medium">
                  {contentInsights.topic_analysis.main_topic}
                </div>
              </div>
              
              {contentInsights.topic_analysis.keywords && (
                <div>
                  <span className="text-sm text-gray-500">关键词:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {contentInsights.topic_analysis.keywords.slice(0, 5).map((keyword: string, index: number) => (
                      <span 
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>

        {/* 评论分析摘要 */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <span className="mr-2">💬</span>
            评论分析摘要
          </h3>
          
          {commentInsights.total_comments ? (
            <div className="space-y-4">
              <div>
                <span className="text-sm text-gray-500">评论总数:</span>
                <div className="font-medium text-lg">
                  {formatNumber(commentInsights.total_comments)}
                </div>
              </div>

              {commentInsights.sentiment_distribution && (
                <div>
                  <span className="text-sm text-gray-500">情感分布:</span>
                  <div className="mt-2 space-y-1">
                    {Object.entries(commentInsights.sentiment_distribution).map(([sentiment, count]) => {
                      const total = Object.values(commentInsights.sentiment_distribution).reduce((a: any, b: any) => a + b, 0);
                      const percentage = total > 0 ? ((count as number) / total * 100).toFixed(1) : '0';
                      
                      return (
                        <div key={sentiment} className="flex justify-between items-center">
                          <span className="text-sm capitalize">
                            {sentiment === 'positive' ? '积极' : 
                             sentiment === 'negative' ? '消极' : '中性'}:
                          </span>
                          <span className="font-medium">{percentage}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {commentInsights.author_engagement && (
                <div>
                  <span className="text-sm text-gray-500">作者互动:</span>
                  <div className="font-medium">
                    回复率 {(commentInsights.author_engagement.reply_rate * 100).toFixed(1)}%
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">暂无评论分析数据</p>
          )}
        </Card>
      </div>

      {/* 综合洞察 */}
      {result.comprehensive_insights && result.comprehensive_insights.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <span className="mr-2">💡</span>
            综合洞察
          </h3>
          <div className="space-y-3">
            {result.comprehensive_insights.map((insight: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>
                <p className="text-gray-700">{insight}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 改进建议 */}
      {result.recommendations && result.recommendations.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <span className="mr-2">🎯</span>
            改进建议
          </h3>
          <div className="space-y-3">
            {result.recommendations.map((recommendation: string, index: number) => (
              <div key={index} className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm font-medium">
                  {index + 1}
                </div>
                <p className="text-gray-700">{recommendation}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
```

## 验收标准

### 功能验收
- [ ] 实时进度显示正常
- [ ] 分析结果完整展示
- [ ] 数据可视化清晰直观
- [ ] 导出功能正常工作
- [ ] 响应式设计适配各种设备
- [ ] 用户交互流畅

### 技术验收
- [ ] 页面加载时间 < 3秒
- [ ] WebSocket连接稳定
- [ ] 组件渲染性能良好
- [ ] 数据更新实时性好
- [ ] 错误处理完善

### 质量验收
- [ ] 组件测试覆盖率 ≥ 70%
- [ ] 可访问性标准符合WCAG 2.1 AA
- [ ] UI设计一致性
- [ ] 用户体验流畅
- [ ] 代码遵循项目规范

## 测试要求

### 组件测试
```typescript
// __tests__/components/ResultDisplay.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ResultDisplay } from '@/components/analysis/ResultDisplay';

const mockResult = {
  summary: {
    video_title: 'Test Video',
    channel_title: 'Test Channel',
    duration: 300,
    view_count: 1000
  },
  content_insights: {
    summary: 'Test content summary'
  },
  comment_insights: {
    total_comments: 50
  }
};

describe('ResultDisplay', () => {
  it('renders all tabs correctly', () => {
    render(<ResultDisplay result={mockResult} videoUrl="https://youtube.com/test" />);
    
    expect(screen.getByText('总览')).toBeInTheDocument();
    expect(screen.getByText('内容分析')).toBeInTheDocument();
    expect(screen.getByText('评论分析')).toBeInTheDocument();
    expect(screen.getByText('导出')).toBeInTheDocument();
  });

  it('switches tabs correctly', () => {
    render(<ResultDisplay result={mockResult} videoUrl="https://youtube.com/test" />);
    
    const contentTab = screen.getByText('内容分析');
    fireEvent.click(contentTab);
    
    // 验证内容分析视图是否显示
    expect(screen.getByText('Test content summary')).toBeInTheDocument();
  });
});
```

## 交付物清单

- [ ] 分析结果页面 (src/app/analyze/[taskId]/page.tsx)
- [ ] 进度跟踪组件 (src/components/analysis/ProgressTracker.tsx)
- [ ] 结果展示组件 (src/components/analysis/ResultDisplay.tsx)
- [ ] 视频总览组件 (src/components/analysis/VideoSummary.tsx)
- [ ] 内容分析视图组件 (src/components/analysis/ContentAnalysisView.tsx)
- [ ] 评论分析视图组件 (src/components/analysis/CommentAnalysisView.tsx)
- [ ] 导出选项组件 (src/components/analysis/ExportOptions.tsx)
- [ ] 数据可视化组件
- [ ] 响应式样式
- [ ] 组件测试文件

## 关键接口

完成此任务后，需要为后续任务提供：
- 完整的结果展示界面
- 实时进度更新能力
- 数据导出功能
- 用户友好的交互体验

## 预估时间

- 开发时间: 4-5天
- 测试时间: 1天
- UI/UX优化: 1天
- 文档时间: 0.5天
- 总计: 6.5-7.5天

## 注意事项

1. 确保界面设计直观易用
2. 实现良好的加载状态和错误处理
3. 优化大量数据的展示性能
4. 确保响应式设计在各种设备上的表现
5. 提供有意义的数据可视化

这是用户最终看到的界面，请确保用户体验的优秀和数据展示的清晰。
