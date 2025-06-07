'use client';

import React, { useState } from 'react';
import { Card } from '@/components/ui';
import { Button } from '@/components/ui';
import { Badge } from '@/components/ui/Badge';
import { AnalysisResult, ExportFormat } from '@/types/analysis';
import { exportToJSON, exportToCSV, exportToPDF } from '@/utils/export';

interface ExportOptionsProps {
  result: AnalysisResult;
  className?: string;
}

export const ExportOptions: React.FC<ExportOptionsProps> = ({
  result,
  className = ''
}) => {
  const [exporting, setExporting] = useState<ExportFormat | null>(null);
  const [exportHistory, setExportHistory] = useState<Array<{
    format: ExportFormat;
    timestamp: Date;
    filename: string;
  }>>([]);

  const handleExport = async (format: ExportFormat) => {
    setExporting(format);
    
    try {
      let filename: string;
      
      switch (format) {
        case 'json':
          filename = await exportToJSON(result);
          break;
        case 'csv':
          filename = await exportToCSV(result);
          break;
        case 'pdf':
          filename = await exportToPDF(result);
          break;
        default:
          throw new Error(`不支持的导出格式: ${format}`);
      }

      setExportHistory(prev => [{
        format,
        timestamp: new Date(),
        filename
      }, ...prev.slice(0, 9)]);

    } catch (error) {
      console.error('导出失败:', error);
      alert(`导出失败: ${error instanceof Error ? error.message : '未知错误'}`);
    } finally {
      setExporting(null);
    }
  };

  const formatFileSize = (result: AnalysisResult) => {
    const jsonSize = JSON.stringify(result).length;
    if (jsonSize < 1024) return `${jsonSize} B`;
    if (jsonSize < 1024 * 1024) return `${(jsonSize / 1024).toFixed(1)} KB`;
    return `${(jsonSize / (1024 * 1024)).toFixed(1)} MB`;
  };

  const exportFormats = [
    {
      format: 'json' as ExportFormat,
      name: 'JSON',
      description: '完整的分析数据，包含所有原始信息',
      icon: '📄',
      size: formatFileSize(result),
      features: ['完整数据', '机器可读', '便于二次处理']
    },
    {
      format: 'csv' as ExportFormat,
      name: 'CSV',
      description: '表格格式，适合在Excel中查看和分析',
      icon: '📊',
      size: '预估 < 1MB',
      features: ['表格格式', 'Excel兼容', '数据分析友好']
    },
    {
      format: 'pdf' as ExportFormat,
      name: 'PDF',
      description: '格式化报告，包含图表和可视化内容',
      icon: '📋',
      size: '预估 2-5MB',
      features: ['可视化图表', '格式化报告', '便于分享']
    }
  ];

  return (
    <div className={`space-y-6 p-6 ${className}`}>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {exportFormats.map((exportFormat) => (
          <Card key={exportFormat.format} className="p-6 hover:shadow-lg transition-shadow">
            <div className="text-center mb-4">
              <div className="text-4xl mb-2">{exportFormat.icon}</div>
              <h3 className="text-lg font-semibold">{exportFormat.name}</h3>
              <p className="text-sm text-gray-600 mt-1">{exportFormat.description}</p>
            </div>

            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">预估大小:</span>
                <Badge variant="secondary">{exportFormat.size}</Badge>
              </div>
              
              <div>
                <p className="text-sm text-gray-600 mb-2">特性:</p>
                <ul className="text-xs text-gray-500 space-y-1">
                  {exportFormat.features.map((feature, index) => (
                    <li key={index}>• {feature}</li>
                  ))}
                </ul>
              </div>
            </div>

            <Button
              onClick={() => handleExport(exportFormat.format)}
              disabled={exporting !== null}
              className="w-full"
              variant={exporting === exportFormat.format ? "secondary" : "primary"}
            >
              {exporting === exportFormat.format ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>导出中...</span>
                </div>
              ) : (
                `导出 ${exportFormat.name}`
              )}
            </Button>
          </Card>
        ))}
      </div>

      {exportHistory.length > 0 && (
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center">
            <span className="mr-2">📋</span>
            导出历史
          </h3>
          <div className="space-y-3">
            {exportHistory.map((record, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Badge variant="outline">{record.format.toUpperCase()}</Badge>
                  <span className="text-sm font-medium">{record.filename}</span>
                </div>
                <div className="text-xs text-gray-500">
                  {record.timestamp.toLocaleString('zh-CN')}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card className="p-6 bg-blue-50 border-blue-200">
        <h3 className="text-lg font-semibold mb-3 text-blue-800">导出说明</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-700">
          <div>
            <h4 className="font-medium mb-2">数据完整性</h4>
            <ul className="space-y-1 text-xs">
              <li>• JSON格式包含完整的原始数据</li>
              <li>• CSV格式适合数据分析和处理</li>
              <li>• PDF格式提供可视化报告</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">使用建议</h4>
            <ul className="space-y-1 text-xs">
              <li>• 长期存储建议使用JSON格式</li>
              <li>• 数据分析建议使用CSV格式</li>
              <li>• 分享报告建议使用PDF格式</li>
            </ul>
          </div>
        </div>
      </Card>
    </div>
  );
};
