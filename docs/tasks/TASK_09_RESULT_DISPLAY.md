# Task 9: 结果展示

## 任务概述

实现分析结果展示界面，为用户提供直观、交互式的YouTube视频分析报告。包括实时进度显示、多维度数据可视化、导出功能和响应式设计，确保用户能够轻松理解和使用分析结果。

## 目标

- 设计直观的分析结果展示界面
- 实现实时进度跟踪和状态更新
- 提供多种数据可视化组件
- 支持分析结果的导出和分享
- 确保移动端和桌面端的良好体验

## 可交付成果

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
  const [analysisResult, setAnalysisResult] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const { getTaskById } = useAnalysisStore();
  const task = getTaskById(taskId);

  // WebSocket连接用于实时更新
  const { isConnected } = useWebSocket({
    taskId,
    onMessage: (message) => {
      if (message.type === 'task_completed') {
        setAnalysisResult(message.result);
        setIsLoading(false);
      } else if (message.type === 'task_failed') {
        setError(message.error?.message || '分析失败');
        setIsLoading(false);
      }
    }
  });

  // 获取分析结果
  useEffect(() => {
    const fetchResult = async () => {
      try {
        const response = await fetch(`/api/v1/tasks/${taskId}/result`);
        
        if (response.status === 202) {
          return; // 任务仍在处理中
        }
        
        if (!response.ok) {
          throw new Error('Failed to fetch result');
        }
        
        const data = await response.json();
        setAnalysisResult(data.result);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : '获取结果失败');
        setIsLoading(false);
      }
    };

    fetchResult();
  }, [taskId]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              分析结果
            </h1>
            <p className="text-gray-600">任务ID: {taskId}</p>
          </div>

          {isLoading ? (
            <ProgressTracker 
              task={task} 
              isConnected={isConnected}
            />
          ) : error ? (
            <ErrorDisplay error={error} />
          ) : (
            <ResultDisplay 
              result={analysisResult}
              taskId={taskId}
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

### 2. 进度跟踪组件

```typescript
// src/components/analysis/ProgressTracker.tsx
'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Progress } from '@/components/ui/Progress';

interface ProgressTrackerProps {
  task: any;
  isConnected: boolean;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  task,
  isConnected
}) => {
  const analysisSteps = [
    { id: 'extraction', name: 'YouTube数据提取', icon: '📥' },
    { id: 'transcription', name: '音频转录', icon: '🎵' },
    { id: 'content_analysis', name: '内容分析', icon: '📝' },
    { id: 'comment_analysis', name: '评论分析', icon: '💬' },
    { id: 'finalization', name: '生成报告', icon: '📊' }
  ];

  const getCurrentStepIndex = () => {
    if (!task?.currentStep) return 0;
    const stepName = task.currentStep.toLowerCase();
    return analysisSteps.findIndex(step => 
      stepName.includes(step.id) || stepName.includes(step.name)
    );
  };

  const currentStepIndex = getCurrentStepIndex();
  const progress = task?.progress || 0;

  return (
    <div className="space-y-6">
      {/* 连接状态指示器 */}
      <Card className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm text-gray-600">
              {isConnected ? '实时连接正常' : '连接断开'}
            </span>
          </div>
          <div className="text-sm text-gray-500">
            进度: {progress}%
          </div>
        </div>
      </Card>

      {/* 整体进度条 */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">分析进度</h2>
        <Progress value={progress} className="mb-4" />
        <p className="text-gray-600 text-center">
          {task?.currentStep || '准备开始分析...'}
        </p>
      </Card>

      {/* 步骤详情 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">分析步骤</h3>
        <div className="space-y-4">
          {analysisSteps.map((step, index) => (
            <div
              key={step.id}
              className={`flex items-center space-x-4 p-3 rounded-lg ${
                index < currentStepIndex
                  ? 'bg-green-50 border border-green-200'
                  : index === currentStepIndex
                  ? 'bg-blue-50 border border-blue-200'
                  : 'bg-gray-50 border border-gray-200'
              }`}
            >
              <div className="text-2xl">{step.icon}</div>
              <div className="flex-1">
                <div className="font-medium">{step.name}</div>
                <div className="text-sm text-gray-500">
                  {index < currentStepIndex
                    ? '已完成'
                    : index === currentStepIndex
                    ? '进行中...'
                    : '等待中'
                  }
                </div>
              </div>
              <div className="flex items-center">
                {index < currentStepIndex && (
                  <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm">✓</span>
                  </div>
                )}
                {index === currentStepIndex && (
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 预估时间 */}
      {task?.estimatedTimeRemaining && (
        <Card className="p-4">
          <div className="text-center">
            <div className="text-sm text-gray-500">预计剩余时间</div>
            <div className="text-lg font-semibold">
              {Math.ceil(task.estimatedTimeRemaining / 60)} 分钟
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};
```

### 3. 结果展示组件

```typescript
// src/components/analysis/ResultDisplay.tsx
'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { VideoSummary } from './VideoSummary';
import { ContentAnalysisView } from './ContentAnalysisView';
import { CommentAnalysisView } from './CommentAnalysisView';
import { ExportOptions } from './ExportOptions';

interface ResultDisplayProps {
  result: any;
  taskId: string;
}

export const ResultDisplay: React.FC<ResultDisplayProps> = ({
  result,
  taskId
}) => {
  const [activeTab, setActiveTab] = useState('summary');

  const tabs = [
    { id: 'summary', name: '总结概览', icon: '📋' },
    { id: 'content', name: '内容分析', icon: '📝' },
    { id: 'comments', name: '评论分析', icon: '💬' },
    { id: 'export', name: '导出选项', icon: '📤' }
  ];

  if (!result) {
    return (
      <Card className="p-8 text-center">
        <div className="text-gray-500">暂无分析结果</div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* 标签导航 */}
      <Card className="p-1">
        <div className="flex space-x-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-3 px-4 rounded-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span>{tab.icon}</span>
              <span className="font-medium">{tab.name}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* 内容区域 */}
      <div className="min-h-96">
        {activeTab === 'summary' && (
          <VideoSummary 
            summary={result.summary}
            insights={result.comprehensive_insights}
            recommendations={result.recommendations}
          />
        )}
        
        {activeTab === 'content' && (
          <ContentAnalysisView 
            contentInsights={result.content_insights}
          />
        )}
        
        {activeTab === 'comments' && (
          <CommentAnalysisView 
            commentInsights={result.comment_insights}
          />
        )}
        
        {activeTab === 'export' && (
          <ExportOptions 
            result={result}
            taskId={taskId}
          />
        )}
      </div>

      {/* 快速操作 */}
      <Card className="p-4">
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            分析完成时间: {new Date(result.summary?.analysis_timestamp).toLocaleString()}
          </div>
          <div className="flex space-x-2">
            <Button
              variant="secondary"
              onClick={() => window.location.href = '/'}
            >
              分析新视频
            </Button>
            <Button
              onClick={() => setActiveTab('export')}
            >
              导出结果
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
```

### 4. 视频总结组件

```typescript
// src/components/analysis/VideoSummary.tsx
'use client';

import { Card } from '@/components/ui/Card';

interface VideoSummaryProps {
  summary: any;
  insights: string[];
  recommendations: string[];
}

export const VideoSummary: React.FC<VideoSummaryProps> = ({
  summary,
  insights,
  recommendations
}) => {
  return (
    <div className="space-y-6">
      {/* 视频基本信息 */}
      <Card className="p-6">
        <h2 className="text-2xl font-bold mb-4">视频概览</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {Math.floor((summary?.duration || 0) / 60)}分钟
            </div>
            <div className="text-sm text-gray-600">视频时长</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {(summary?.view_count || 0).toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">观看次数</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {new Date(summary?.analysis_timestamp).toLocaleDateString()}
            </div>
            <div className="text-sm text-gray-600">分析日期</div>
          </div>
        </div>
      </Card>

      {/* 综合洞察 */}
      {insights && insights.length > 0 && (
        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-4">🔍 关键洞察</h3>
          <div className="space-y-3">
            {insights.map((insight, index) => (
              <div
                key={index}
                className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
              >
                <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                  {index + 1}
                </div>
                <div className="flex-1 text-gray-700">{insight}</div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 改进建议 */}
      {recommendations && recommendations.length > 0 && (
        <Card className="p-6">
          <h3 className="text-xl font-semibold mb-4">💡 改进建议</h3>
          <div className="space-y-3">
            {recommendations.map((recommendation, index) => (
              <div
                key={index}
                className="flex items-start space-x-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200"
              >
                <div className="text-yellow-600 text-xl">💡</div>
                <div className="flex-1 text-gray-700">{recommendation}</div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
```

### 5. 导出功能组件

```typescript
// src/components/analysis/ExportOptions.tsx
'use client';

import { useState } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

interface ExportOptionsProps {
  result: any;
  taskId: string;
}

export const ExportOptions: React.FC<ExportOptionsProps> = ({
  result,
  taskId
}) => {
  const [isExporting, setIsExporting] = useState(false);

  const exportFormats = [
    {
      id: 'json',
      name: 'JSON格式',
      description: '完整的结构化数据，适合程序处理',
      icon: '📄'
    },
    {
      id: 'pdf',
      name: 'PDF报告',
      description: '格式化的分析报告，适合分享和打印',
      icon: '📑'
    },
    {
      id: 'markdown',
      name: 'Markdown文档',
      description: '文本格式报告，适合文档编辑',
      icon: '📝'
    },
    {
      id: 'csv',
      name: 'CSV数据',
      description: '表格数据，适合数据分析',
      icon: '📊'
    }
  ];

  const handleExport = async (format: string) => {
    setIsExporting(true);
    
    try {
      const response = await fetch(`/api/v1/tasks/${taskId}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ format })
      });
      
      if (!response.ok) {
        throw new Error('Export failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analysis_${taskId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
    } catch (error) {
      console.error('Export failed:', error);
      alert('导出失败，请重试');
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = async () => {
    const shareUrl = `${window.location.origin}/analyze/${taskId}`;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: '视频分析结果',
          text: '查看这个YouTube视频的分析结果',
          url: shareUrl
        });
      } catch (error) {
        console.log('分享取消');
      }
    } else {
      // 复制到剪贴板
      navigator.clipboard.writeText(shareUrl);
      alert('链接已复制到剪贴板');
    }
  };

  return (
    <div className="space-y-6">
      {/* 导出格式选择 */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">选择导出格式</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {exportFormats.map((format) => (
            <div
              key={format.id}
              className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-start space-x-3">
                <div className="text-2xl">{format.icon}</div>
                <div className="flex-1">
                  <h3 className="font-semibold">{format.name}</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    {format.description}
                  </p>
                  <Button
                    size="sm"
                    onClick={() => handleExport(format.id)}
                    disabled={isExporting}
                  >
                    {isExporting ? '导出中...' : '导出'}
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* 分享选项 */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">分享结果</h2>
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div>
            <h3 className="font-medium">分享分析结果</h3>
            <p className="text-sm text-gray-600">
              生成可分享的链接，其他人可以查看这个分析结果
            </p>
          </div>
          <Button onClick={handleShare}>
            分享链接
          </Button>
        </div>
      </Card>

      {/* 数据统计 */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">数据统计</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="text-lg font-bold text-blue-600">
              {result.content_insights?.key_points?.length || 0}
            </div>
            <div className="text-sm text-gray-600">关键要点</div>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <div className="text-lg font-bold text-green-600">
              {result.content_insights?.topics?.length || 0}
            </div>
            <div className="text-sm text-gray-600">主要主题</div>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <div className="text-lg font-bold text-purple-600">
              {result.comment_insights?.total_comments || 0}
            </div>
            <div className="text-sm text-gray-600">分析评论</div>
          </div>
          <div className="p-3 bg-orange-50 rounded-lg">
            <div className="text-lg font-bold text-orange-600">
              {result.comment_insights?.author_engagement?.total_replies || 0}
            </div>
            <div className="text-sm text-gray-600">作者回复</div>
          </div>
        </div>
      </Card>
    </div>
  );
};
```

## 依赖关系

### 前置条件
- Task 1: 项目配置管理（必须完成）
- Task 3: 前端UI框架（必须完成）
- Task 8: 分析编排器（必须完成，需要完整的分析结果）

### 阻塞任务
- 无（这是最后的展示层）

## 验收标准

### 功能验收
- [ ] 实时进度跟踪正确显示
- [ ] 分析结果完整展示
- [ ] 多标签页导航正常工作
- [ ] 数据可视化清晰易懂
- [ ] 导出功能正常工作
- [ ] 分享功能正常工作
- [ ] 响应式设计适配各种设备

### 技术验收
- [ ] 页面加载时间 < 3秒
- [ ] WebSocket连接稳定
- [ ] 组件渲染性能良好
- [ ] 导出文件格式正确
- [ ] 移动端体验良好

### 质量验收
- [ ] 组件测试覆盖率 ≥ 70%
- [ ] 可访问性标准符合WCAG 2.1 AA
- [ ] 用户体验测试通过
- [ ] 视觉设计一致性
- [ ] 代码遵循项目规范

## 测试要求

### 组件测试
```typescript
// __tests__/components/ResultDisplay.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ResultDisplay } from '@/components/analysis/ResultDisplay';

const mockResult = {
  summary: {
    video_title: '测试视频',
    duration: 300,
    view_count: 1000
  },
  content_insights: {
    key_points: [{ text: '测试要点', importance: 0.9 }],
    summary: '测试总结'
  },
  comment_insights: {
    total_comments: 50,
    sentiment_distribution: { positive: 30, neutral: 15, negative: 5 }
  }
};

describe('ResultDisplay', () => {
  it('renders all tabs correctly', () => {
    render(<ResultDisplay result={mockResult} taskId="test-id" />);
    
    expect(screen.getByText('总结概览')).toBeInTheDocument();
    expect(screen.getByText('内容分析')).toBeInTheDocument();
    expect(screen.getByText('评论分析')).toBeInTheDocument();
    expect(screen.getByText('导出选项')).toBeInTheDocument();
  });

  it('switches tabs correctly', () => {
    render(<ResultDisplay result={mockResult} taskId="test-id" />);
    
    fireEvent.click(screen.getByText('内容分析'));
    // 验证内容分析标签页内容显示
  });

  it('displays video summary correctly', () => {
    render(<ResultDisplay result={mockResult} taskId="test-id" />);
    
    expect(screen.getByText('测试视频')).toBeInTheDocument();
    expect(screen.getByText('5分钟')).toBeInTheDocument(); // 300秒 = 5分钟
  });
});
```

## 预估工作量

- **开发时间**: 4-5天
- **测试时间**: 1.5天
- **UI/UX优化**: 1天
- **响应式适配**: 0.5天
- **文档时间**: 0.5天
- **总计**: 7.5天

## 关键路径

此任务是用户界面的最终展示层，完成后用户即可看到完整的分析结果。

## 交付检查清单

- [ ] 分析结果页面已实现
- [ ] 进度跟踪组件已完成
- [ ] 结果展示组件已完成
- [ ] 数据可视化组件已实现
- [ ] 导出功能已实现
- [ ] 分享功能已实现
- [ ] 响应式设计已完成
- [ ] 组件测试通过
- [ ] 用户体验测试通过
- [ ] 代码已提交并通过CI检查

## 后续任务接口

完成此任务后，用户将能够：
- 实时查看分析进度
- 浏览完整的分析结果
- 导出多种格式的报告
- 分享分析结果
- 在各种设备上良好使用

这是整个YouTube分析工具的最终用户界面，为用户提供完整的分析体验。
