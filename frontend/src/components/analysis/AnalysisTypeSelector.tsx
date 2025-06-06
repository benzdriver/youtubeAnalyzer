'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui';
import { Button } from '@/components/ui';

interface AnalysisType {
  id: string;
  name: string;
  description: string;
  icon: string;
  features: string[];
  estimatedTime: number;
  category: 'content' | 'social' | 'comprehensive' | 'custom';
}

const analysisTypes: AnalysisType[] = [
  {
    id: 'content',
    name: '内容分析',
    description: '分析视频内容、结构和关键信息',
    icon: '📝',
    features: ['转录文本', '关键要点', '主题分类', '情感分析'],
    estimatedTime: 180,
    category: 'content'
  },
  {
    id: 'comments',
    name: '评论分析',
    description: '分析用户评论和作者回复',
    icon: '💬',
    features: ['评论情感', '作者回复', '热门评论', '主题提取'],
    estimatedTime: 120,
    category: 'social'
  },
  {
    id: 'comprehensive',
    name: '综合分析',
    description: '包含内容和评论的完整分析',
    icon: '🔍',
    features: ['全部功能', '深度洞察', '完整报告', '数据导出'],
    estimatedTime: 300,
    category: 'comprehensive'
  }
];

interface AnalysisTypeSelectorProps {
  selectedType: string;
  onTypeChange: (type: string) => void;
  className?: string;
}

export const AnalysisTypeSelector: React.FC<AnalysisTypeSelectorProps> = ({
  selectedType,
  onTypeChange,
  className
}) => {
  const [expandedType, setExpandedType] = useState<string | null>(null);

  return (
    <div className={className}>
      <h2 className="text-2xl font-semibold mb-4">选择分析类型</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {analysisTypes.map((type) => (
          <Card
            key={type.id}
            className={`cursor-pointer transition-all duration-200 ${
              selectedType === type.id
                ? 'ring-2 ring-blue-500 bg-blue-50'
                : 'hover:shadow-md'
            }`}
            onClick={() => onTypeChange(type.id)}
          >
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{type.icon}</span>
                  <h3 className="font-semibold text-lg">{type.name}</h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e?.stopPropagation();
                    setExpandedType(
                      expandedType === type.id ? null : type.id
                    );
                  }}
                >
                  {expandedType === type.id ? '收起' : '详情'}
                </Button>
              </div>
              
              <p className="text-gray-600 text-sm mb-3">{type.description}</p>
              
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>预计时间: {Math.floor(type.estimatedTime / 60)}分钟</span>
                <span className="px-2 py-1 bg-gray-100 rounded-full text-xs">
                  {type.category}
                </span>
              </div>
              
              {expandedType === type.id && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="font-medium mb-2">功能特性:</h4>
                  <ul className="space-y-1">
                    {type.features.map((feature, index) => (
                      <li key={index} className="flex items-center text-sm">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                        {feature}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};
