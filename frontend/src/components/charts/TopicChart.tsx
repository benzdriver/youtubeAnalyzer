'use client';

import React, { useEffect, useRef } from 'react';
import { Chart, ChartConfiguration, registerables } from 'chart.js';

Chart.register(...registerables);

interface TopicData {
  word: string;
  weight: number;
  category?: string;
  color?: string;
}

interface TopicChartProps {
  topics: TopicData[];
  maxWords?: number;
  colorScheme?: string[];
  onWordClick?: (word: string) => void;
  chartType?: 'bar' | 'bubble' | 'wordcloud';
  className?: string;
}

export const TopicChart: React.FC<TopicChartProps> = ({
  topics,
  maxWords = 20,
  colorScheme = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4'],
  onWordClick,
  chartType = 'bar',
  className = ''
}) => {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstanceRef = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current || !topics.length) return;

    if (chartInstanceRef.current) {
      chartInstanceRef.current.destroy();
    }

    const ctx = chartRef.current.getContext('2d');
    if (!ctx) return;

    const sortedTopics = [...topics]
      .sort((a, b) => b.weight - a.weight)
      .slice(0, maxWords);

    const labels = sortedTopics.map(topic => topic.word);
    const data = sortedTopics.map(topic => topic.weight);
    const colors = sortedTopics.map((topic, index) => 
      topic.color || colorScheme[index % colorScheme.length]
    );

    let config: ChartConfiguration;

    if (chartType === 'bubble') {
      config = {
        type: 'bubble',
        data: {
          datasets: [{
            label: '主题权重',
            data: sortedTopics.map((topic) => ({
              x: Math.random() * 100,
              y: Math.random() * 100,
              r: Math.max(5, topic.weight * 20)
            })),
            backgroundColor: colors.map(color => color + '80'),
            borderColor: colors,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              display: false
            },
            y: {
              display: false
            }
          },
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const index = context.dataIndex;
                  const topic = sortedTopics[index];
                  return `${topic.word}: ${topic.weight.toFixed(2)}`;
                }
              }
            }
          },
          onClick: (event, elements) => {
            if (elements.length > 0 && onWordClick) {
              const index = elements[0].index;
              const topic = sortedTopics[index];
              onWordClick(topic.word);
            }
          }
        }
      };
    } else {
      config = {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: '主题权重',
            data,
            backgroundColor: colors.map(color => color + '80'),
            borderColor: colors,
            borderWidth: 2,
            borderRadius: 4,
            borderSkipped: false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          indexAxis: chartType === 'bar' ? 'y' : 'x',
          scales: {
            x: {
              beginAtZero: true,
              title: {
                display: true,
                text: '权重'
              },
              grid: {
                color: '#E5E7EB'
              }
            },
            y: {
              title: {
                display: true,
                text: '主题'
              },
              grid: {
                color: '#E5E7EB'
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
                  return `权重: ${context.parsed.x.toFixed(2)}`;
                }
              }
            }
          },
          onClick: (event, elements) => {
            if (elements.length > 0 && onWordClick) {
              const index = elements[0].index;
              const topic = sortedTopics[index];
              onWordClick(topic.word);
            }
          }
        }
      };
    }

    chartInstanceRef.current = new Chart(ctx, config);

    return () => {
      if (chartInstanceRef.current) {
        chartInstanceRef.current.destroy();
        chartInstanceRef.current = null;
      }
    };
  }, [topics, maxWords, colorScheme, onWordClick, chartType]);

  return (
    <div className={`relative h-64 ${className}`}>
      <canvas ref={chartRef} />
      {topics.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-gray-500">
          暂无主题数据
        </div>
      )}
    </div>
  );
};

export default TopicChart;
