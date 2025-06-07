'use client';

import React from 'react';
import { Card } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';
import { AnalysisResult } from '@/types/analysis';

interface VideoSummaryProps {
  result: AnalysisResult;
  videoUrl: string;
  className?: string;
}

export const VideoSummary: React.FC<VideoSummaryProps> = ({
  result,
  videoUrl,
  className = ''
}) => {
  const { videoInfo, contentInsights, commentInsights } = result;

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
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  };

  return (
    <div className={`space-y-6 p-6 ${className}`} role="region" aria-label="视频概览信息">
      {/* 视频基本信息 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 视频缩略图和基本信息 */}
        <div className="lg:col-span-2">
          <Card className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              {videoInfo.thumbnailUrl && (
                <div className="flex-shrink-0">
                  <img
                    src={videoInfo.thumbnailUrl}
                    alt={`${videoInfo.title} 的缩略图`}
                    className="w-full sm:w-48 h-auto rounded-lg"
                    loading="lazy"
                  />
                </div>
              )}
              <div className="flex-1 space-y-3">
                <h2 className="text-xl font-semibold text-gray-900 line-clamp-2">
                  {videoInfo.title}
                </h2>
                <p className="text-gray-600">
                  频道: {videoInfo.channelTitle}
                </p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">
                    时长: {formatDuration(videoInfo.duration)}
                  </Badge>
                  {videoInfo.viewCount && (
                    <Badge variant="secondary">
                      观看: {formatNumber(videoInfo.viewCount)}
                    </Badge>
                  )}
                  {videoInfo.likeCount && (
                    <Badge variant="secondary">
                      点赞: {formatNumber(videoInfo.likeCount)}
                    </Badge>
                  )}
                  {videoInfo.commentCount && (
                    <Badge variant="secondary">
                      评论: {formatNumber(videoInfo.commentCount)}
                    </Badge>
                  )}
                </div>
                <a
                  href={videoUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 rounded"
                  aria-label={`在新窗口中查看原视频: ${videoInfo.title}`}
                >
                  <span className="mr-1" aria-hidden="true">🔗</span>
                  查看原视频
                </a>
              </div>
            </div>
          </Card>
        </div>

        {/* 分析质量指标 */}
        <div>
          <Card className="p-4">
            <h3 className="text-lg font-semibold mb-4">质量指标</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">内容质量</span>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${contentInsights.qualityScore}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {Math.round(contentInsights.qualityScore)}%
                  </span>
                </div>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">社区健康度</span>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-600 h-2 rounded-full"
                      style={{ width: `${commentInsights.communityHealth}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {Math.round(commentInsights.communityHealth)}%
                  </span>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <span className="text-gray-600">参与度</span>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full"
                      style={{ width: `${commentInsights.authorEngagement.engagementRate * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium">
                    {Math.round(commentInsights.authorEngagement.engagementRate * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* 快速洞察 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">📝</div>
          <div className="text-2xl font-bold text-blue-600">
            {contentInsights.keyPoints.length}
          </div>
          <div className="text-sm text-gray-600">关键要点</div>
        </Card>

        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">🏷️</div>
          <div className="text-2xl font-bold text-green-600">
            {contentInsights.topics.length}
          </div>
          <div className="text-sm text-gray-600">主要话题</div>
        </Card>

        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">💬</div>
          <div className="text-2xl font-bold text-purple-600">
            {commentInsights.totalComments}
          </div>
          <div className="text-sm text-gray-600">总评论数</div>
        </Card>

        <Card className="p-4 text-center">
          <div className="text-2xl mb-2">🎯</div>
          <div className="text-2xl font-bold text-orange-600">
            {commentInsights.topThemes.length}
          </div>
          <div className="text-sm text-gray-600">热门主题</div>
        </Card>
      </div>

      {/* 情感分析概览 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">情感分析概览</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 内容情感 */}
          <div>
            <h4 className="font-medium mb-3">内容情感</h4>
            <div className="flex items-center space-x-3">
              <div className={`w-4 h-4 rounded-full ${
                contentInsights.sentiment.overall === 'positive' ? 'bg-green-500' :
                contentInsights.sentiment.overall === 'negative' ? 'bg-red-500' : 'bg-gray-500'
              }`} />
              <span className="capitalize font-medium">
                {contentInsights.sentiment.overall === 'positive' ? '积极' :
                 contentInsights.sentiment.overall === 'negative' ? '消极' : '中性'}
              </span>
              <span className="text-sm text-gray-600">
                (置信度: {Math.round(contentInsights.sentiment.confidence * 100)}%)
              </span>
            </div>
          </div>

          {/* 评论情感分布 */}
          <div>
            <h4 className="font-medium mb-3">评论情感分布</h4>
            <div className="space-y-2">
              {Object.entries(commentInsights.sentimentDistribution).map(([sentiment, count]) => (
                <div key={sentiment} className="flex justify-between items-center">
                  <span className="text-sm capitalize">
                    {sentiment === 'positive' ? '积极' :
                     sentiment === 'negative' ? '消极' : '中性'}
                  </span>
                  <span className="text-sm font-medium">{count as number}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
