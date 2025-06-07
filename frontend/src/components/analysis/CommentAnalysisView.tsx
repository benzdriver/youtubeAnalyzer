'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';

import { SentimentChart } from '@/components/charts/SentimentChart';
import { EngagementChart } from '@/components/charts/EngagementChart';
import { CommentInsights } from '@/types/analysis';

interface CommentAnalysisViewProps {
  insights: CommentInsights;
  viewMode?: 'overview' | 'sentiment' | 'themes' | 'engagement';
  onThemeClick?: (theme: string) => void;
  onSentimentFilter?: (sentiment: string) => void;
  className?: string;
}

export const CommentAnalysisView: React.FC<CommentAnalysisViewProps> = ({
  insights,

  onThemeClick,
  onSentimentFilter,
  className = ''
}) => {
  const [selectedTheme, setSelectedTheme] = useState<string | null>(null);
  const [selectedSentiment, setSelectedSentiment] = useState<string | null>(null);

  const handleThemeClick = (theme: string) => {
    const newTheme = selectedTheme === theme ? null : theme;
    setSelectedTheme(newTheme);
    onThemeClick?.(theme);
  };

  const handleSentimentFilter = (sentiment: string) => {
    const newSentiment = selectedSentiment === sentiment ? null : sentiment;
    setSelectedSentiment(newSentiment);
    onSentimentFilter?.(sentiment);
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  const formatTime = (hours: number) => {
    if (hours < 1) {
      return `${Math.round(hours * 60)}分钟`;
    }
    if (hours < 24) {
      return `${hours.toFixed(1)}小时`;
    }
    return `${(hours / 24).toFixed(1)}天`;
  };

  return (
    <div className={`space-y-6 p-6 ${className}`}>
      {/* 评论概览统计 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">💬</div>
          <div className="text-2xl font-bold text-blue-600">
            {formatNumber(insights.totalComments)}
          </div>
          <div className="text-sm text-gray-600">总评论数</div>
        </Card>

        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">🎯</div>
          <div className="text-2xl font-bold text-green-600">
            {insights.topThemes.length}
          </div>
          <div className="text-sm text-gray-600">热门主题</div>
        </Card>

        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">💝</div>
          <div className="text-2xl font-bold text-purple-600">
            {insights.authorEngagement.totalReplies}
          </div>
          <div className="text-sm text-gray-600">作者回复</div>
        </Card>

        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">🏥</div>
          <div className="text-2xl font-bold text-orange-600">
            {Math.round(insights.communityHealth)}%
          </div>
          <div className="text-sm text-gray-600">社区健康度</div>
        </Card>
      </div>

      {/* 情感分析图表 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">📊</span>
          情感分布分析
        </h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <SentimentChart 
              sentimentData={insights.sentimentDistribution}
              onSegmentClick={handleSentimentFilter}
            />
          </div>
          <div className="space-y-4">
            <h4 className="font-medium">情感分类详情</h4>
            {Object.entries(insights.sentimentDistribution).map(([sentiment, count]) => {
              const percentage = ((count as number) / insights.totalComments * 100).toFixed(1);
              const isSelected = selectedSentiment === sentiment;
              
              return (
                <div
                  key={sentiment}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                  onClick={() => handleSentimentFilter(sentiment)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <div className={`w-4 h-4 rounded-full ${
                        sentiment === 'positive' ? 'bg-green-500' :
                        sentiment === 'negative' ? 'bg-red-500' : 'bg-gray-500'
                      }`} />
                      <span className="font-medium capitalize">
                        {sentiment === 'positive' ? '积极' :
                         sentiment === 'negative' ? '消极' : '中性'}
                      </span>
                    </div>
                    <div className="text-right">
                      <div className="font-bold">{formatNumber(count as number)}</div>
                      <div className="text-sm text-gray-600">{percentage}%</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* 热门主题 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">🔥</span>
          热门讨论主题
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {insights.topThemes.map((theme, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border cursor-pointer transition-all ${
                selectedTheme === theme 
                  ? 'bg-blue-50 border-blue-200 shadow-md' 
                  : 'bg-white border-gray-200 hover:bg-gray-50 hover:shadow-sm'
              }`}
              onClick={() => handleThemeClick(theme)}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{theme}</span>
                <Badge variant="secondary" className="text-xs">
                  #{index + 1}
                </Badge>
              </div>
            </div>
          ))}
        </div>
        {selectedTheme && (
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              已选择主题: <strong>{selectedTheme}</strong>
            </p>
            <p className="text-xs text-blue-600 mt-1">
              点击其他主题进行切换，或再次点击取消选择
            </p>
          </div>
        )}
      </Card>

      {/* 作者参与度分析 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">👤</span>
          作者参与度分析
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center text-xl font-bold bg-blue-100 text-blue-600">
              {insights.authorEngagement.totalReplies}
            </div>
            <h4 className="font-medium mb-1">总回复数</h4>
            <p className="text-sm text-gray-600">作者回复评论总数</p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center text-xl font-bold bg-green-100 text-green-600">
              {formatTime(insights.authorEngagement.averageResponseTime)}
            </div>
            <h4 className="font-medium mb-1">平均响应时间</h4>
            <p className="text-sm text-gray-600">作者回复的平均时间</p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 rounded-full mx-auto mb-3 flex items-center justify-center text-xl font-bold bg-purple-100 text-purple-600">
              {Math.round(insights.authorEngagement.engagementRate * 100)}%
            </div>
            <h4 className="font-medium mb-1">参与度</h4>
            <p className="text-sm text-gray-600">作者与观众的互动程度</p>
          </div>
        </div>

        {/* 参与度图表 */}
        <div className="mt-6">
          <h4 className="font-medium mb-3">参与度趋势</h4>
          <EngagementChart 
            engagementData={[
              { time: new Date(), value: insights.authorEngagement.engagementRate, type: 'replies' }
            ]}
          />
        </div>
      </Card>

      {/* 社区健康度评估 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center">
          <span className="mr-2">🏥</span>
          社区健康度评估
        </h3>
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-700">健康度评分</span>
              <span className="text-sm text-gray-600">{Math.round(insights.communityHealth)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full transition-all duration-300 ${
                  insights.communityHealth >= 80 ? 'bg-green-500' :
                  insights.communityHealth >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${insights.communityHealth}%` }}
              />
            </div>
          </div>
          <div className="text-right">
            <div className={`text-2xl ${
              insights.communityHealth >= 80 ? 'text-green-500' :
              insights.communityHealth >= 60 ? 'text-yellow-500' : 'text-red-500'
            }`}>
              {insights.communityHealth >= 80 ? '🌟' :
               insights.communityHealth >= 60 ? '⭐' : '💫'}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {insights.communityHealth >= 80 ? '健康' :
               insights.communityHealth >= 60 ? '良好' : '需关注'}
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="p-3 bg-gray-50 rounded-lg">
            <h5 className="font-medium mb-2">评估指标</h5>
            <ul className="space-y-1 text-gray-600">
              <li>• 积极评论比例</li>
              <li>• 建设性讨论程度</li>
              <li>• 作者互动质量</li>
              <li>• 社区参与活跃度</li>
            </ul>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <h5 className="font-medium mb-2">改进建议</h5>
            <ul className="space-y-1 text-gray-600">
              {insights.communityHealth < 60 && (
                <>
                  <li>• 增加作者回复频率</li>
                  <li>• 引导积极讨论</li>
                </>
              )}
              {insights.communityHealth >= 60 && insights.communityHealth < 80 && (
                <>
                  <li>• 保持当前互动水平</li>
                  <li>• 鼓励深度讨论</li>
                </>
              )}
              {insights.communityHealth >= 80 && (
                <>
                  <li>• 社区状态良好</li>
                  <li>• 继续保持互动</li>
                </>
              )}
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};
