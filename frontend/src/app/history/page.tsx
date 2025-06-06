'use client';

import React, { useState } from 'react';
import { useAnalysisStore } from '@/store/analysisStore';
import { Card, Button } from '@/components/ui';
import { AnalysisTask, TaskStatus } from '@/types/analysis';

export default function HistoryPage() {
  const { taskHistory, deleteTask } = useAnalysisStore();
  const [selectedTask, setSelectedTask] = useState<AnalysisTask | null>(null);

  const getStatusColor = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case TaskStatus.FAILED:
        return 'bg-red-100 text-red-800';
      case TaskStatus.PROCESSING:
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const handleTaskClick = (task: AnalysisTask) => {
    setSelectedTask(task);
  };

  const handleDeleteTask = (taskId: string) => {
    if (confirm('确定要删除这个分析任务吗？')) {
      deleteTask(taskId);
      if (selectedTask?.id === taskId) {
        setSelectedTask(null);
      }
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">分析历史</h1>

        {taskHistory.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-gray-600 mb-2">暂无分析记录</h2>
            <p className="text-gray-500 mb-6">开始您的第一个YouTube视频分析</p>
            <Button onClick={() => window.location.href = '/'}>
              开始分析
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <h2 className="text-xl font-semibold mb-4">任务列表</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {taskHistory.map((task) => (
                  <Card
                    key={task.id}
                    className={`cursor-pointer transition-all ${
                      selectedTask?.id === task.id ? 'ring-2 ring-blue-500' : 'hover:shadow-md'
                    }`}
                    onClick={() => handleTaskClick(task)}
                  >
                    <div className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className={`px-2 py-1 rounded-full text-xs ${getStatusColor(task.status)}`}>
                          {task.status}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatDate(task.createdAt)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 truncate">
                        {task.url}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-500">
                          {task.type}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e?.stopPropagation();
                            handleDeleteTask(task.id);
                          }}
                        >
                          删除
                        </Button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>

            <div className="lg:col-span-2">
              {selectedTask ? (
                <div>
                  <h2 className="text-xl font-semibold mb-4">任务详情</h2>
                  <Card>
                    <div className="p-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div>
                          <h3 className="font-medium mb-3">基本信息</h3>
                          <div className="space-y-2 text-sm">
                            <div>
                              <span className="text-gray-600">任务ID:</span>
                              <span className="ml-2 font-mono">{selectedTask.id}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">分析类型:</span>
                              <span className="ml-2">{selectedTask.type}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">状态:</span>
                              <span className={`ml-2 px-2 py-1 rounded-full text-xs ${getStatusColor(selectedTask.status)}`}>
                                {selectedTask.status}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">进度:</span>
                              <span className="ml-2">{selectedTask.progress}%</span>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h3 className="font-medium mb-3">时间信息</h3>
                          <div className="space-y-2 text-sm">
                            <div>
                              <span className="text-gray-600">创建时间:</span>
                              <span className="ml-2">{formatDate(selectedTask.createdAt)}</span>
                            </div>
                            <div>
                              <span className="text-gray-600">更新时间:</span>
                              <span className="ml-2">{formatDate(selectedTask.updatedAt)}</span>
                            </div>
                            {selectedTask.completedAt && (
                              <div>
                                <span className="text-gray-600">完成时间:</span>
                                <span className="ml-2">{formatDate(selectedTask.completedAt.toString())}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>

                      <div className="mb-6">
                        <h3 className="font-medium mb-3">视频链接</h3>
                        <a
                          href={selectedTask.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-800 break-all text-sm"
                        >
                          {selectedTask.url}
                        </a>
                      </div>

                      {selectedTask.result && (
                        <div className="mb-6">
                          <h3 className="font-medium mb-3">分析结果</h3>
                          <div className="bg-gray-50 rounded-lg p-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                              <div>
                                <h4 className="font-medium text-sm mb-2">视频信息</h4>
                                <div className="space-y-1 text-xs">
                                  <div>标题: {selectedTask.result.videoInfo.title}</div>
                                  <div>频道: {selectedTask.result.videoInfo.channelTitle}</div>
                                  <div>时长: {Math.floor(selectedTask.result.videoInfo.duration / 60)}分钟</div>
                                </div>
                              </div>
                              <div>
                                <h4 className="font-medium text-sm mb-2">内容洞察</h4>
                                <div className="space-y-1 text-xs">
                                  <div>质量评分: {selectedTask.result.contentInsights.qualityScore}/100</div>
                                  <div>情感倾向: {selectedTask.result.contentInsights.sentiment.overall}</div>
                                  <div>关键要点: {selectedTask.result.contentInsights.keyPoints.length}个</div>
                                </div>
                              </div>
                            </div>
                            <div>
                              <h4 className="font-medium text-sm mb-2">内容摘要</h4>
                              <p className="text-xs text-gray-700 leading-relaxed">
                                {selectedTask.result.contentInsights.summary}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {selectedTask.error && (
                        <div className="mb-6">
                          <h3 className="font-medium mb-3 text-red-800">错误信息</h3>
                          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                            <p className="text-sm text-red-700">{selectedTask.error}</p>
                          </div>
                        </div>
                      )}

                      <div className="flex justify-end space-x-3">
                        <Button
                          variant="outline"
                          onClick={() => setSelectedTask(null)}
                        >
                          关闭
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => handleDeleteTask(selectedTask.id)}
                        >
                          删除任务
                        </Button>
                      </div>
                    </div>
                  </Card>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-gray-400 text-4xl mb-4">👈</div>
                  <p className="text-gray-500">选择左侧的任务查看详情</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
