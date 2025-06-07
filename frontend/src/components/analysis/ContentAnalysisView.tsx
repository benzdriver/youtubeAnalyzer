'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui';
import { ContentInsights, KeyPoint } from '@/types/analysis';

interface ContentAnalysisViewProps {
  insights: ContentInsights;
  viewMode?: 'summary' | 'detailed' | 'timeline';
  onKeyPointClick?: (keyPoint: KeyPoint) => void;
  onTopicClick?: (topic: string) => void;
  className?: string;
}

export const ContentAnalysisView: React.FC<ContentAnalysisViewProps> = ({
  insights,
  onKeyPointClick,
  onTopicClick,
  className = ''
}) => {
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [expandedKeyPoints, setExpandedKeyPoints] = useState<Set<number>>(new Set());

  const formatTimestamp = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const toggleKeyPoint = (index: number) => {
    const newExpanded = new Set(expandedKeyPoints);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedKeyPoints(newExpanded);
  };

  const handleTopicClick = (topic: string) => {
    setSelectedTopic(selectedTopic === topic ? null : topic);
    onTopicClick?.(topic);
  };

  const getImportanceColor = (importance: number) => {
    if (importance >= 0.8) return 'bg-red-100 text-red-800 border-red-200';
    if (importance >= 0.6) return 'bg-orange-100 text-orange-800 border-orange-200';
    if (importance >= 0.4) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getImportanceLabel = (importance: number) => {
    if (importance >= 0.8) return '高';
    if (importance >= 0.6) return '中';
    if (importance >= 0.4) return '低';
    return '一般';
  };

  return (
    <div className={`space-y-6 p-6 ${className}`} role="region" aria-label="内容分析详情">
      {/* 内容摘要 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center" id="content-summary">
          <span className="mr-2" aria-hidden="true">📄</span>
          内容摘要
        </h3>
        <p className="text-gray-700 leading-relaxed" aria-labelledby="content-summary">{insights.summary}</p>
      </Card>

      {/* 主要话题 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">🏷️</span>
          主要话题
        </h3>
        <div className="flex flex-wrap gap-2">
          {insights.topics.map((topic, index) => (
            <Badge
              key={index}
              variant={selectedTopic === topic ? "primary" : "secondary"}
              className="cursor-pointer hover:bg-blue-100 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded"
              onClick={() => handleTopicClick(topic)}
              onKeyDown={(e: React.KeyboardEvent) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleTopicClick(topic);
                }
              }}
              tabIndex={0}
              role="button"
              aria-pressed={selectedTopic === topic}
              aria-label={`话题: ${topic}${selectedTopic === topic ? ' (已选择)' : ''}`}
            >
              {topic}
            </Badge>
          ))}
        </div>
        {selectedTopic && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              已选择话题: <strong>{selectedTopic}</strong>
            </p>
            <p className="text-xs text-blue-600 mt-1">
              点击其他话题进行切换，或再次点击取消选择
            </p>
          </div>
        )}
      </Card>

      {/* 关键要点 */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold flex items-center">
            <span className="mr-2">📝</span>
            关键要点
          </h3>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpandedKeyPoints(new Set())}
            >
              收起全部
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExpandedKeyPoints(new Set(insights.keyPoints.map((_, i) => i)))}
            >
              展开全部
            </Button>
          </div>
        </div>

        <div className="space-y-3">
          {insights.keyPoints
            .sort((a, b) => b.importance - a.importance)
            .map((keyPoint, index) => (
              <div
                key={index}
                className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                  expandedKeyPoints.has(index) ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200'
                }`}
                onClick={() => {
                  toggleKeyPoint(index);
                  onKeyPointClick?.(keyPoint);
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <span className="text-sm font-medium text-blue-600">
                        {formatTimestamp(keyPoint.timestamp)}
                      </span>
                      <Badge
                        variant="outline"
                        className={getImportanceColor(keyPoint.importance)}
                      >
                        重要性: {getImportanceLabel(keyPoint.importance)}
                      </Badge>
                    </div>
                    <p className={`text-gray-700 ${
                      expandedKeyPoints.has(index) ? '' : 'line-clamp-2'
                    }`}>
                      {keyPoint.content}
                    </p>
                  </div>
                  <div className="flex-shrink-0 ml-4">
                    <span className="text-gray-400">
                      {expandedKeyPoints.has(index) ? '▼' : '▶'}
                    </span>
                  </div>
                </div>
                
                {expandedKeyPoints.has(index) && (
                  <div className="mt-3 pt-3 border-t border-blue-200">
                    <div className="flex items-center justify-between text-sm text-gray-600">
                      <span>时间戳: {formatTimestamp(keyPoint.timestamp)}</span>
                      <span>重要性评分: {(keyPoint.importance * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                )}
              </div>
            ))}
        </div>
      </Card>

      {/* 情感分析详情 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">😊</span>
          情感分析
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className={`w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center text-2xl ${
              insights.sentiment.overall === 'positive' ? 'bg-green-100 text-green-600' :
              insights.sentiment.overall === 'negative' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'
            }`}>
              {insights.sentiment.overall === 'positive' ? '😊' :
               insights.sentiment.overall === 'negative' ? '😞' : '😐'}
            </div>
            <h4 className="font-medium mb-1">整体情感</h4>
            <p className="text-sm text-gray-600 capitalize">
              {insights.sentiment.overall === 'positive' ? '积极' :
               insights.sentiment.overall === 'negative' ? '消极' : '中性'}
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center text-xl font-bold bg-blue-100 text-blue-600">
              {Math.round(insights.sentiment.score * 100)}
            </div>
            <h4 className="font-medium mb-1">情感评分</h4>
            <p className="text-sm text-gray-600">
              {insights.sentiment.score > 0 ? '偏积极' : insights.sentiment.score < 0 ? '偏消极' : '中性'}
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center text-xl font-bold bg-purple-100 text-purple-600">
              {Math.round(insights.sentiment.confidence * 100)}%
            </div>
            <h4 className="font-medium mb-1">置信度</h4>
            <p className="text-sm text-gray-600">
              {insights.sentiment.confidence > 0.8 ? '高' :
               insights.sentiment.confidence > 0.6 ? '中' : '低'}
            </p>
          </div>
        </div>
      </Card>

      {/* 质量评估 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">⭐</span>
          内容质量评估
        </h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">质量评分</span>
              <span className="text-sm text-gray-600">{Math.round(insights.qualityScore)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-300 ${
                  insights.qualityScore >= 80 ? 'bg-green-500' :
                  insights.qualityScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${insights.qualityScore}%` }}
              />
            </div>
          </div>
          <div className="text-right">
            <div className={`text-2xl ${
              insights.qualityScore >= 80 ? 'text-green-500' :
              insights.qualityScore >= 60 ? 'text-yellow-500' : 'text-red-500'
            }`}>
              {insights.qualityScore >= 80 ? '🌟' :
               insights.qualityScore >= 60 ? '⭐' : '💫'}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {insights.qualityScore >= 80 ? '优秀' :
               insights.qualityScore >= 60 ? '良好' : '需改进'}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
};
