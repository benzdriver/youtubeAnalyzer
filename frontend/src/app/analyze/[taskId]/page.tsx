'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { useAnalysisStore } from '@/store/analysisStore';
import { useAnalysisWebSocket } from '@/hooks/useWebSocket';
import { ProgressTracker } from '@/components/analysis/ProgressTracker';
import { ResultDisplay } from '@/components/analysis/ResultDisplay';
import { Card, Button } from '@/components/ui';
import { TaskStatus } from '@/types/analysis';

export default function AnalyzePage() {
  const params = useParams();
  const taskId = params.taskId as string;
  
  const { taskHistory, currentTask } = useAnalysisStore();
  const { connected, reconnecting } = useAnalysisWebSocket(taskId);

  const task = currentTask?.id === taskId ? currentTask : taskHistory.find(t => t.id === taskId);

  if (!task) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">任务未找到</h1>
          <p className="text-gray-600 mb-6">指定的分析任务不存在或已被删除</p>
          <Button onClick={() => window.location.href = '/'}>
            返回首页
          </Button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.PROCESSING:
        return 'bg-blue-100 text-blue-800';
      case TaskStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case TaskStatus.FAILED:
        return 'bg-red-100 text-red-800';
      case TaskStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case TaskStatus.CANCELLED:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900">分析进度</h1>
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${
                connected ? 'bg-green-500' : reconnecting ? 'bg-yellow-500' : 'bg-red-500'
              }`} />
              <span className="text-sm text-gray-600">
                {connected ? '实时连接' : reconnecting ? '重连中' : '连接断开'}
              </span>
            </div>
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <span>任务ID: {task.id}</span>
            <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(task.status)}`}>
              {task.status}
            </span>
            <span>创建时间: {new Date(task.createdAt).toLocaleString('zh-CN')}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4">视频信息</h2>
                <div className="space-y-3">
                  <div>
                    <span className="text-gray-600">链接:</span>
                    <a
                      href={task.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-blue-600 hover:text-blue-800 break-all"
                    >
                      {task.url}
                    </a>
                  </div>
                  <div>
                    <span className="text-gray-600">分析类型:</span>
                    <span className="ml-2">{task.type}</span>
                  </div>
                  {task.options.maxComments && (
                    <div>
                      <span className="text-gray-600">最大评论数:</span>
                      <span className="ml-2">{task.options.maxComments}</span>
                    </div>
                  )}
                  {task.options.language && (
                    <div>
                      <span className="text-gray-600">语言:</span>
                      <span className="ml-2">{task.options.language}</span>
                    </div>
                  )}
                </div>
              </div>
            </Card>

            {task.status === TaskStatus.COMPLETED && task.result && (
              <ResultDisplay 
                result={task.result}
                videoUrl={task.input.youtube_url}
              />
            )}

            {task.status === TaskStatus.FAILED && (
              <Card>
                <div className="p-6">
                  <h2 className="text-xl font-semibold text-red-800 mb-4">分析失败</h2>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                    <p className="text-red-700">
                      {task.error || '分析过程中发生未知错误'}
                    </p>
                  </div>
                  <div className="flex justify-center space-x-4">
                    <Button onClick={() => window.location.href = '/'}>
                      重新开始
                    </Button>
                    <Button variant="outline" onClick={() => window.location.href = '/history'}>
                      查看历史
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </div>

          <div className="lg:col-span-1">
            <ProgressTracker
              taskId={task.id}
              steps={task.steps}
              currentStep={task.currentStep}
              progress={task.progress}
              showDetails={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
