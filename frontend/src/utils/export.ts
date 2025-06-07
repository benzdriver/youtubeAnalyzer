import { saveAs } from 'file-saver';
import { AnalysisResult } from '@/types/analysis';
import { analysisApi } from './api';

export const exportToJSON = async (result: AnalysisResult): Promise<string> => {
  try {
    if (result.taskId) {
      const blob = await analysisApi.exportResult(result.taskId, 'json');
      const filename = `analysis-${result.taskId}.json`;
      saveAs(blob, filename);
      return filename;
    }
  } catch (error) {
    console.warn('API export failed, falling back to client-side export:', error);
  }

  const jsonData = JSON.stringify(result, null, 2);
  const blob = new Blob([jsonData], { type: 'application/json' });
  const filename = `analysis-${Date.now()}.json`;
  
  saveAs(blob, filename);
  return filename;
};

export const exportToCSV = async (result: AnalysisResult): Promise<string> => {
  try {
    if (result.taskId) {
      const blob = await analysisApi.exportResult(result.taskId, 'csv');
      const filename = `analysis-${result.taskId}.csv`;
      saveAs(blob, filename);
      return filename;
    }
  } catch (error) {
    console.warn('API export failed, falling back to client-side export:', error);
  }

  const csvRows: string[] = [];
  
  csvRows.push('Category,Key,Value,Details');
  
  csvRows.push(`Video Info,Title,"${result.videoInfo.title}",`);
  csvRows.push(`Video Info,Channel,"${result.videoInfo.channelTitle}",`);
  csvRows.push(`Video Info,Duration,${result.videoInfo.duration},seconds`);
  csvRows.push(`Video Info,Views,${result.videoInfo.viewCount || 0},`);
  csvRows.push(`Video Info,Likes,${result.videoInfo.likeCount || 0},`);
  csvRows.push(`Video Info,Comments,${result.videoInfo.commentCount || 0},`);
  
  csvRows.push(`Content,Summary,"${result.contentInsights.summary.replace(/"/g, '""')}",`);
  csvRows.push(`Content,Quality Score,${result.contentInsights.qualityScore},%`);
  csvRows.push(`Content,Sentiment,"${result.contentInsights.sentiment.overall}",confidence: ${result.contentInsights.sentiment.confidence}`);
  
  result.contentInsights.topics.forEach((topic, index) => {
    csvRows.push(`Content,Topic ${index + 1},"${topic}",`);
  });
  
  result.contentInsights.keyPoints.forEach((point, index) => {
    csvRows.push(`Content,Key Point ${index + 1},"${point.content.replace(/"/g, '""')}",timestamp: ${point.timestamp}s, importance: ${point.importance}`);
  });
  
  csvRows.push(`Comments,Total Comments,${result.commentInsights.totalComments},`);
  csvRows.push(`Comments,Community Health,${result.commentInsights.communityHealth},%`);
  csvRows.push(`Comments,Author Replies,${result.commentInsights.authorEngagement.totalReplies},`);
  csvRows.push(`Comments,Engagement Rate,${result.commentInsights.authorEngagement.engagementRate},`);
  csvRows.push(`Comments,Avg Response Time,${result.commentInsights.authorEngagement.averageResponseTime},hours`);
  
  Object.entries(result.commentInsights.sentimentDistribution).forEach(([sentiment, count]) => {
    csvRows.push(`Comments,Sentiment ${sentiment},${count},`);
  });
  
  result.commentInsights.topThemes.forEach((theme, index) => {
    csvRows.push(`Comments,Theme ${index + 1},"${theme}",`);
  });
  
  result.comprehensiveInsights?.forEach((insight, index) => {
    csvRows.push(`Insights,Insight ${index + 1},"${insight.replace(/"/g, '""')}",`);
  });
  
  result.recommendations?.forEach((recommendation, index) => {
    csvRows.push(`Recommendations,Recommendation ${index + 1},"${recommendation.replace(/"/g, '""')}",`);
  });
  
  const csvContent = csvRows.join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const filename = `analysis-${Date.now()}.csv`;
  
  saveAs(blob, filename);
  return filename;
};

export const exportToPDF = async (result: AnalysisResult): Promise<string> => {
  
  const htmlContent = `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>YouTube视频分析报告</title>
      <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        .header { text-align: center; margin-bottom: 30px; }
        .section { margin-bottom: 25px; }
        .section h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        .video-info { background: #f8f9fa; padding: 15px; border-radius: 5px; }
        .key-point { margin: 10px 0; padding: 10px; background: #e9ecef; border-radius: 3px; }
        .insight { margin: 8px 0; padding: 8px; background: #d1ecf1; border-radius: 3px; }
        .recommendation { margin: 8px 0; padding: 8px; background: #d4edda; border-radius: 3px; }
      </style>
    </head>
    <body>
      <div class="header">
        <h1>YouTube视频分析报告</h1>
        <p>生成时间: ${new Date().toLocaleString('zh-CN')}</p>
      </div>
      
      <div class="section">
        <h2>视频信息</h2>
        <div class="video-info">
          <p><strong>标题:</strong> ${result.videoInfo.title}</p>
          <p><strong>频道:</strong> ${result.videoInfo.channelTitle}</p>
          <p><strong>时长:</strong> ${Math.floor(result.videoInfo.duration / 60)}:${(result.videoInfo.duration % 60).toString().padStart(2, '0')}</p>
          <p><strong>观看数:</strong> ${result.videoInfo.viewCount?.toLocaleString() || 'N/A'}</p>
          <p><strong>点赞数:</strong> ${result.videoInfo.likeCount?.toLocaleString() || 'N/A'}</p>
          <p><strong>评论数:</strong> ${result.videoInfo.commentCount?.toLocaleString() || 'N/A'}</p>
        </div>
      </div>
      
      <div class="section">
        <h2>内容分析</h2>
        <p><strong>内容摘要:</strong> ${result.contentInsights.summary}</p>
        <p><strong>质量评分:</strong> ${result.contentInsights.qualityScore}%</p>
        <p><strong>整体情感:</strong> ${result.contentInsights.sentiment.overall} (置信度: ${Math.round(result.contentInsights.sentiment.confidence * 100)}%)</p>
        
        <h3>主要话题</h3>
        <ul>
          ${result.contentInsights.topics.map(topic => `<li>${topic}</li>`).join('')}
        </ul>
        
        <h3>关键要点</h3>
        ${result.contentInsights.keyPoints.map((point, index) => `
          <div class="key-point">
            <strong>要点 ${index + 1}</strong> (${Math.floor(point.timestamp / 60)}:${(point.timestamp % 60).toString().padStart(2, '0')})<br>
            ${point.content}
          </div>
        `).join('')}
      </div>
      
      <div class="section">
        <h2>评论分析</h2>
        <p><strong>总评论数:</strong> ${result.commentInsights.totalComments}</p>
        <p><strong>社区健康度:</strong> ${result.commentInsights.communityHealth}%</p>
        <p><strong>作者回复数:</strong> ${result.commentInsights.authorEngagement.totalReplies}</p>
        <p><strong>参与度:</strong> ${Math.round(result.commentInsights.authorEngagement.engagementRate * 100)}%</p>
        
        <h3>情感分布</h3>
        <ul>
          ${Object.entries(result.commentInsights.sentimentDistribution).map(([sentiment, count]) => 
            `<li>${sentiment === 'positive' ? '积极' : sentiment === 'negative' ? '消极' : '中性'}: ${count}</li>`
          ).join('')}
        </ul>
        
        <h3>热门主题</h3>
        <ul>
          ${result.commentInsights.topThemes.map(theme => `<li>${theme}</li>`).join('')}
        </ul>
      </div>
      
      ${result.comprehensiveInsights && result.comprehensiveInsights.length > 0 ? `
        <div class="section">
          <h2>综合洞察</h2>
          ${result.comprehensiveInsights.map((insight, index) => `
            <div class="insight">
              <strong>洞察 ${index + 1}:</strong> ${insight}
            </div>
          `).join('')}
        </div>
      ` : ''}
      
      ${result.recommendations && result.recommendations.length > 0 ? `
        <div class="section">
          <h2>改进建议</h2>
          ${result.recommendations.map((recommendation, index) => `
            <div class="recommendation">
              <strong>建议 ${index + 1}:</strong> ${recommendation}
            </div>
          `).join('')}
        </div>
      ` : ''}
    </body>
    </html>
  `;
  
  const blob = new Blob([htmlContent], { type: 'text/html' });
  const filename = `analysis-report-${Date.now()}.html`;
  
  saveAs(blob, filename);
  return filename;
};
