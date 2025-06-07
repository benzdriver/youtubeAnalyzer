'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui';
import { VideoSummary } from './VideoSummary';
import { ContentAnalysisView } from './ContentAnalysisView';
import { CommentAnalysisView } from './CommentAnalysisView';
import { ExportOptions } from './ExportOptions';
import { Tabs } from '@/components/ui/Tabs';
import { AnalysisResult } from '@/types/analysis';

interface ResultDisplayProps {
  result: AnalysisResult;
  videoUrl: string;
  className?: string;
}

export const ResultDisplay: React.FC<ResultDisplayProps> = ({
  result,
  videoUrl,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    {
      id: 'overview',
      label: '总览',
      icon: '📊',
      content: <VideoSummary result={result} videoUrl={videoUrl} />
    },
    {
      id: 'content',
      label: '内容分析',
      icon: '📝',
      content: <ContentAnalysisView insights={result.contentInsights} />
    },
    {
      id: 'comments',
      label: '评论分析',
      icon: '💬',
      content: <CommentAnalysisView insights={result.commentInsights} />
    },
    {
      id: 'export',
      label: '导出',
      icon: '📤',
      content: <ExportOptions result={result} />
    }
  ];

  return (
    <div className={`space-y-6 ${className}`} role="main" aria-label="分析结果展示">
      {/* 综合洞察 */}
      {result.comprehensiveInsights && result.comprehensiveInsights.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center" id="comprehensive-insights">
            <span className="mr-2" aria-hidden="true">💡</span>
            综合洞察
          </h3>
          <div className="space-y-3" role="list" aria-labelledby="comprehensive-insights">
            {result.comprehensiveInsights.map((insight: string, index: number) => (
              <div key={index} className="flex items-start space-x-3" role="listitem">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium" aria-label={`洞察 ${index + 1}`}>
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
          <h3 className="text-lg font-semibold mb-4 flex items-center" id="recommendations">
            <span className="mr-2" aria-hidden="true">🎯</span>
            改进建议
          </h3>
          <div className="space-y-3" role="list" aria-labelledby="recommendations">
            {result.recommendations.map((recommendation: string, index: number) => (
              <div key={index} className="flex items-start space-x-3" role="listitem">
                <div className="flex-shrink-0 w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-sm font-medium" aria-label={`建议 ${index + 1}`}>
                  {index + 1}
                </div>
                <p className="text-gray-700">{recommendation}</p>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* 详细分析标签页 */}
      <Card className="p-0">
        <Tabs
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          className="min-h-[600px]"
          aria-label="详细分析内容"
        />
      </Card>
    </div>
  );
};
