'use client';

import React, { useEffect, useRef } from 'react';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

Chart.register(...registerables);

interface QualityMetrics {
  contentQuality: number;
  engagement: number;
  sentiment: number;
  originality: number;
  clarity: number;
  relevance: number;
}

interface QualityRadarChartProps {
  qualityMetrics: QualityMetrics;
  maxValue?: number;
  showGrid?: boolean;
  onMetricClick?: (metric: string) => void;
  className?: string;
  showLabels?: boolean;
  showValues?: boolean;
}

export const QualityRadarChart: React.FC<QualityRadarChartProps> = ({
  qualityMetrics,
  maxValue = 100,
  showGrid = true,
  onMetricClick,
  className = '',
  showLabels = true,
  showValues = true
}) => {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstanceRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current) return;

    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const labels = [
      '内容质量',
      '参与度',
      '情感倾向',
      '原创性',
      '清晰度',
      '相关性'
    ];

    const data = [
      qualityMetrics.contentQuality,
      qualityMetrics.engagement,
      qualityMetrics.sentiment,
      qualityMetrics.originality,
      qualityMetrics.clarity,
      qualityMetrics.relevance
    ];

    const config: ChartConfiguration = {
      type: 'radar',
      data: {
        labels,
        datasets: [{
          label: '质量指标',
          data,
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          borderColor: 'rgb(59, 130, 246)',
          borderWidth: 2,
          pointBackgroundColor: 'rgb(59, 130, 246)',
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointHoverBackgroundColor: 'rgb(37, 99, 235)',
          pointHoverBorderColor: '#fff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            max: maxValue,
            min: 0,
            ticks: {
              stepSize: maxValue / 5,
              display: showValues,
              font: {
                size: 10
              },
              color: '#6B7280'
            },
            grid: {
              display: showGrid,
              color: '#E5E7EB'
            },
            angleLines: {
              display: showGrid,
              color: '#E5E7EB'
            },
            pointLabels: {
              display: showLabels,
              font: {
                size: 12,
                weight: 500
              },
              color: '#374151'
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed.r;
                const percentage = ((value / maxValue) * 100).toFixed(1);
                return `${context.label}: ${value.toFixed(1)} (${percentage}%)`;
              }
            }
          }
        },
        onClick: (event, elements) => {
          if (elements.length > 0 && onMetricClick) {
            const index = elements[0].index;
            const metricKeys = Object.keys(qualityMetrics);
            const metric = metricKeys[index];
            onMetricClick(metric);
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
  }, [qualityMetrics, maxValue, showGrid, onMetricClick, showLabels, showValues]);

  const overallScore = Object.values(qualityMetrics).reduce((sum, value) => sum + value, 0) / Object.values(qualityMetrics).length;
  const scorePercentage = (overallScore / maxValue) * 100;

  const getScoreColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    if (percentage >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreBadge = (percentage: number) => {
    if (percentage >= 80) return '优秀';
    if (percentage >= 60) return '良好';
    if (percentage >= 40) return '一般';
    return '需改进';
  };

  return (
    <div className={`relative ${className}`}>
      <div className="h-64 mb-4">
        <canvas ref={chartRef} />
      </div>
      
      {/* Overall Score Display */}
      <div className="text-center">
        <div className="inline-flex items-center space-x-2">
          <span className="text-sm text-gray-600">综合评分:</span>
          <span className={`text-lg font-bold ${getScoreColor(scorePercentage)}`}>
            {overallScore.toFixed(1)}
          </span>
          <span className="text-sm text-gray-500">/ {maxValue}</span>
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
            scorePercentage >= 80 ? 'bg-green-100 text-green-800' :
            scorePercentage >= 60 ? 'bg-yellow-100 text-yellow-800' :
            scorePercentage >= 40 ? 'bg-orange-100 text-orange-800' :
            'bg-red-100 text-red-800'
          }`}>
            {getScoreBadge(scorePercentage)}
          </span>
        </div>
      </div>

      {/* Metric Details */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
        {Object.entries(qualityMetrics).map(([key, value]) => {
          const labels = {
            contentQuality: '内容质量',
            engagement: '参与度',
            sentiment: '情感倾向',
            originality: '原创性',
            clarity: '清晰度',
            relevance: '相关性'
          };
          
          const percentage = (value / maxValue) * 100;
          
          return (
            <div key={key} className="flex justify-between items-center">
              <span className="text-gray-600">
                {labels[key as keyof typeof labels]}:
              </span>
              <span className={`font-medium ${getScoreColor(percentage)}`}>
                {value.toFixed(1)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default QualityRadarChart;
