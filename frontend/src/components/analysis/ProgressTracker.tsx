'use client';

import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui';
import { Progress } from '@/components/ui';
import { AnalysisStep, StepStatus } from '@/types/analysis';

interface ProgressTrackerProps {
  taskId: string;
  steps: AnalysisStep[];
  currentStep?: string;
  progress: number;
  showDetails?: boolean;
  onStepClick?: (step: AnalysisStep) => void;
  className?: string;
}

const stepIcons: Record<string, string> = {
  'video_info': '📹',
  'audio_extraction': '🎵',
  'transcription': '📝',
  'content_analysis': '🔍',
  'comment_extraction': '💬',
  'comment_analysis': '📊',
  'sentiment_analysis': '😊',
  'report_generation': '📄',
  'completed': '✅'
};

const getStepIcon = (stepId: string, status: StepStatus) => {
  if (status === StepStatus.COMPLETED) return '✅';
  if (status === StepStatus.FAILED) return '❌';
  if (status === StepStatus.RUNNING) return '⏳';
  return stepIcons[stepId] || '⭕';
};

const getStepStatusColor = (status: StepStatus) => {
  switch (status) {
    case StepStatus.COMPLETED:
      return 'text-green-600 bg-green-50';
    case StepStatus.RUNNING:
      return 'text-blue-600 bg-blue-50';
    case StepStatus.FAILED:
      return 'text-red-600 bg-red-50';
    case StepStatus.SKIPPED:
      return 'text-gray-400 bg-gray-50';
    default:
      return 'text-gray-500 bg-gray-50';
  }
};

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  taskId,
  steps,
  currentStep,
  progress,
  showDetails = true,
  onStepClick,
  className
}) => {
  const [elapsedTime, setElapsedTime] = useState(0);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<number | null>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const completedSteps = steps.filter(step => step.status === StepStatus.COMPLETED).length;
  const totalSteps = steps.length;
  const currentStepData = steps.find(step => step.id === currentStep);

  return (
    <div className={className}>
      <Card>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold">分析进度</h2>
            <div className="text-sm text-gray-500">
              任务ID: {taskId.slice(-8)}
            </div>
          </div>

          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                总体进度 ({completedSteps}/{totalSteps})
              </span>
              <span className="text-sm text-gray-600">
                {Math.round(progress)}%
              </span>
            </div>
            <Progress
              value={progress}
              variant={progress === 100 ? 'success' : 'default'}
              size="lg"
            />
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">已用时间:</span>
              <span className="font-medium">{formatTime(elapsedTime)}</span>
            </div>
            {estimatedTimeRemaining && (
              <div className="flex items-center justify-between">
                <span className="text-gray-600">预计剩余:</span>
                <span className="font-medium">{formatTime(estimatedTimeRemaining)}</span>
              </div>
            )}
          </div>

          {currentStepData && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">
                  {getStepIcon(currentStepData.id, currentStepData.status)}
                </span>
                <div>
                  <h3 className="font-medium text-blue-900">
                    {currentStepData.name}
                  </h3>
                  <p className="text-sm text-blue-700">
                    {currentStepData.description}
                  </p>
                </div>
              </div>
              {currentStepData.progress > 0 && (
                <div className="mt-3">
                  <Progress
                    value={currentStepData.progress}
                    variant="default"
                    size="sm"
                    showLabel
                  />
                </div>
              )}
            </div>
          )}

          {showDetails && (
            <div className="space-y-3">
              <h3 className="font-medium text-gray-900 mb-3">详细步骤</h3>
              {steps.map((step, index) => (
                <div
                  key={step.id}
                  className={`flex items-center space-x-3 p-3 rounded-lg transition-colors ${
                    onStepClick ? 'cursor-pointer hover:bg-gray-50' : ''
                  } ${step.id === currentStep ? 'bg-blue-50' : 'bg-gray-50'}`}
                  onClick={() => onStepClick?.(step)}
                >
                  <div className="flex-shrink-0">
                    <span className="text-lg">
                      {getStepIcon(step.id, step.status)}
                    </span>
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900 truncate">
                        {step.name}
                      </h4>
                      <span className={`px-2 py-1 text-xs rounded-full ${getStepStatusColor(step.status)}`}>
                        {step.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      {step.description}
                    </p>
                    {step.error && (
                      <p className="text-xs text-red-600 mt-1">
                        错误: {step.error}
                      </p>
                    )}
                  </div>

                  {step.progress > 0 && step.status === StepStatus.RUNNING && (
                    <div className="flex-shrink-0 w-16">
                      <div className="text-xs text-gray-500 text-right">
                        {Math.round(step.progress)}%
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};
