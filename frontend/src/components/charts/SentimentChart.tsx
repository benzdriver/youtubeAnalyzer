'use client';

import React, { useEffect, useRef } from 'react';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

Chart.register(...registerables);

interface SentimentChartProps {
  sentimentData: Record<string, number>;
  chartType?: 'pie' | 'bar' | 'doughnut';
  showLabels?: boolean;
  showPercentages?: boolean;
  onSegmentClick?: (sentiment: string) => void;
  className?: string;
}

export const SentimentChart: React.FC<SentimentChartProps> = ({
  sentimentData,
  chartType = 'doughnut',
  showLabels = true,
  showPercentages = true,
  onSegmentClick,
  className = ''
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

    const labels = Object.keys(sentimentData).map(key => {
      switch (key) {
        case 'positive': return '积极';
        case 'negative': return '消极';
        case 'neutral': return '中性';
        default: return key;
      }
    });

    const data = Object.values(sentimentData);
    const total = data.reduce((sum, value) => sum + value, 0);

    const colors = {
      positive: '#10B981',
      negative: '#EF4444',
      neutral: '#6B7280',
      mixed: '#F59E0B'
    };

    const backgroundColors = Object.keys(sentimentData).map(key => 
      colors[key as keyof typeof colors] || '#9CA3AF'
    );

    const config: ChartConfiguration = {
      type: chartType,
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: backgroundColors,
          borderColor: backgroundColors.map(color => color),
          borderWidth: 2,
          hoverBorderWidth: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: showLabels,
            position: 'bottom',
            labels: {
              padding: 20,
              usePointStyle: true,
              font: {
                size: 12
              },
              generateLabels: (chart) => {
                const original = Chart.defaults.plugins.legend.labels.generateLabels;
                const labels = original.call(this, chart);
                
                if (showPercentages) {
                  labels.forEach((label, index) => {
                    const value = data[index];
                    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
                    label.text = `${label.text}: ${value} (${percentage}%)`;
                  });
                }
                
                return labels;
              }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const value = context.parsed;
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
                return `${context.label}: ${value} (${percentage}%)`;
              }
            }
          }
        },
        onClick: (event, elements) => {
          if (elements.length > 0 && onSegmentClick) {
            const index = elements[0].index;
            const sentiment = Object.keys(sentimentData)[index];
            onSegmentClick(sentiment);
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
  }, [sentimentData, chartType, showLabels, showPercentages, onSegmentClick]);

  return (
    <div className={`relative ${className}`}>
      <canvas ref={chartRef} />
    </div>
  );
};

export default SentimentChart;
