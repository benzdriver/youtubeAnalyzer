'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { useAnalysisStore } from '@/store/analysisStore';
import { useAnalysisWebSocket } from '@/hooks/useWebSocket';
import { ProgressTracker } from '@/components/analysis/ProgressTracker';
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
              <Card>
                <div className="p-6">
                  <h2 className="text-xl font-semibold mb-4">分析结果</h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="font-medium mb-3">视频详情</h3>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-gray-600">标题:</span>
                          <span className="ml-2">{task.result.videoInfo.title}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">频道:</span>
                          <span className="ml-2">{task.result.videoInfo.channelTitle}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">时长:</span>
                          <span className="ml-2">{Math.floor(task.result.videoInfo.duration / 60)}分钟</span>
                        </div>
                        {task.result.videoInfo.viewCount && (
                          <div>
                            <span className="text-gray-600">观看次数:</span>
                            <span className="ml-2">{task.result.videoInfo.viewCount.toLocaleString()}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-medium mb-3">内容洞察</h3>
                      <div className="space-y-2 text-sm">
                        <div>
                          <span className="text-gray-600">质量评分:</span>
                          <span className="ml-2">{task.result.contentInsights.qualityScore}/100</span>
                        </div>
                        <div>
                          <span className="text-gray-600">情感倾向:</span>
                          <span className="ml-2">{task.result.contentInsights.sentiment.overall}</span>
                        </div>
                        <div>
                          <span className="text-gray-600">关键要点:</span>
                          <span className="ml-2">{task.result.contentInsights.keyPoints.length}个</span>
                        </div>
                        <div>
                          <span className="text-gray-600">主题标签:</span>
                          <span className="ml-2">{task.result.contentInsights.topics.length}个</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-6 border-t">
                    <h3 className="font-medium mb-3">内容摘要</h3>
                    <p className="text-sm text-gray-700 leading-relaxed">
                      {task.result.contentInsights.summary}
                    </p>
                  </div>

                  {task.result.contentInsights.keyPoints.length > 0 && (
                    <div className="mt-6 pt-6 border-t">
                      <h3 className="font-medium mb-3">关键要点</h3>
                      <div className="space-y-3">
                        {task.result.contentInsights.keyPoints.slice(0, 5).map((point, index) => (
                          <div key={index} className="flex items-start space-x-3">
                            <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-xs font-medium">
                              {index + 1}
                            </span>
                            <div className="flex-1">
                              <p className="text-sm text-gray-700">{point.content}</p>
                              <span className="text-xs text-gray-500">
                                {Math.floor(point.timestamp / 60)}:{(point.timestamp % 60).toString().padStart(2, '0')}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="mt-6 pt-6 border-t flex justify-center space-x-4">
                    <Button onClick={() => window.location.href = '/'}>
                      开始新分析
                    </Button>
                    <Button variant="outline" onClick={() => window.location.href = '/history'}>
                      查看历史
                    </Button>
                  </div>
                </div>
              </Card>
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
