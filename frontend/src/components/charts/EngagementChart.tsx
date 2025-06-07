'use client';

import React, { useEffect, useRef } from 'react';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

Chart.register(...registerables);

interface EngagementPoint {
  time: Date;
  value: number;
  type: 'likes' | 'comments' | 'replies';
  details?: Record<string, unknown>;
}

interface EngagementChartProps {
  engagementData: EngagementPoint[];
  timeRange?: 'hour' | 'day' | 'week';
  showAverage?: boolean;
  onDataPointHover?: (point: EngagementPoint) => void;
  className?: string;
}

export const EngagementChart: React.FC<EngagementChartProps> = ({
  engagementData,
  timeRange = 'day',
  showAverage = true,
  onDataPointHover,
  className = ''
}) => {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstanceRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current || !engagementData.length) return;

    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const groupedData = engagementData.reduce((acc, point) => {
      if (!acc[point.type]) {
        acc[point.type] = [];
      }
      acc[point.type].push(point);
      return acc;
    }, {} as Record<string, EngagementPoint[]>);

    const datasets = Object.entries(groupedData).map(([type, points]) => {
      const colors = {
        likes: '#EF4444',
        comments: '#3B82F6',
        replies: '#10B981'
      };

      const labels = {
        likes: '点赞',
        comments: '评论',
        replies: '回复'
      };

      return {
        label: labels[type as keyof typeof labels] || type,
        data: points.map(point => ({
          x: point.time.getTime(),
          y: point.value
        })),
        borderColor: colors[type as keyof typeof colors] || '#6B7280',
        backgroundColor: colors[type as keyof typeof colors] || '#6B7280',
        fill: false,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6
      };
    });

    if (showAverage && engagementData.length > 0) {
      const average = engagementData.reduce((sum, point) => sum + point.value, 0) / engagementData.length;
      const timeExtent = [
        Math.min(...engagementData.map(p => p.time.getTime())),
        Math.max(...engagementData.map(p => p.time.getTime()))
      ];

      datasets.push({
        label: '平均值',
        data: [
          { x: timeExtent[0], y: average },
          { x: timeExtent[1], y: average }
        ],
        borderColor: '#9CA3AF',
        backgroundColor: '#9CA3AF',
        fill: false,
        tension: 0,
        pointRadius: 0,
        pointHoverRadius: 0,
        segment: {
          borderDash: [5, 5]
        }
      } as typeof datasets[0]);
    }

    const config: ChartConfiguration = {
      type: 'line',
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            type: 'time',
            time: {
              unit: timeRange,
              displayFormats: {
                hour: 'HH:mm',
                day: 'MM/DD',
                week: 'MM/DD'
              }
            },
            title: {
              display: true,
              text: '时间'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: '参与度'
            }
          }
        },
        plugins: {
          legend: {
            display: true,
            position: 'top'
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              title: (tooltipItems) => {
                const date = new Date(tooltipItems[0].parsed.x);
                return date.toLocaleString('zh-CN');
              },
              label: (context) => {
                return `${context.dataset.label}: ${context.parsed.y}`;
              }
            }
          }
        },
        interaction: {
          mode: 'nearest',
          axis: 'x',
          intersect: false
        },
        onHover: (event, elements) => {
          if (elements.length > 0 && onDataPointHover) {
            const element = elements[0];
            const datasetIndex = element.datasetIndex;
            const dataIndex = element.index;
            const dataset = Object.values(groupedData)[datasetIndex];
            if (dataset && dataset[dataIndex]) {
              onDataPointHover(dataset[dataIndex]);
            }
          }
        }
      }
    };

    chartInstanceRef.current = new Chart(ctx, config);

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [engagementData, timeRange, showAverage, onDataPointHover]);

  return (
    <div className={`relative h-64 ${className}`}>
      <canvas ref={chartRef} />
    </div>
  );
};

export default EngagementChart;
