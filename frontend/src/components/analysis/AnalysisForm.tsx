'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Input } from '@/components/ui';
import { Button } from '@/components/ui';
import { Card } from '@/components/ui';
import { AnalysisTypeSelector } from './AnalysisTypeSelector';
import { AnalysisOptions } from '@/types/analysis';

const youtubeUrlSchema = z.object({
  url: z
    .string()
    .min(1, '请输入YouTube视频链接')
    .refine(
      (url) => {
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|embed\/|v\/)|youtu\.be\/)[\w-]+/;
        return youtubeRegex.test(url);
      },
      '请输入有效的YouTube视频链接'
    ),
  analysisType: z.string().min(1, '请选择分析类型'),
  maxComments: z.number().min(10).max(1000).optional(),
  enableTranscription: z.boolean().optional(),
  language: z.string().optional()
});

type FormData = z.infer<typeof youtubeUrlSchema>;

interface AnalysisFormProps {
  onSubmit: (url: string, options: AnalysisOptions) => void;
  isLoading?: boolean;
  className?: string;
}

export const AnalysisForm: React.FC<AnalysisFormProps> = ({
  onSubmit,
  isLoading = false,
  className
}) => {
  const [selectedType, setSelectedType] = useState('comprehensive');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isValid },
    setValue,
    watch
  } = useForm<FormData>({
    resolver: zodResolver(youtubeUrlSchema),
    defaultValues: {
      analysisType: 'comprehensive',
      maxComments: 100,
      enableTranscription: true,
      language: 'zh-CN'
    },
    mode: 'onChange'
  });

  const watchedUrl = watch('url');

  const onFormSubmit = (data: FormData) => {
    const options: AnalysisOptions = {
      analysisDepth: data.analysisType as 'basic' | 'detailed' | 'comprehensive',
      maxComments: data.maxComments,
      enableTranscription: data.enableTranscription,
      language: data.language,
      includeTimestamps: true
    };

    onSubmit(data.url, options);
  };

  const handleTypeChange = (type: string) => {
    setSelectedType(type);
    setValue('analysisType', type, { shouldValidate: true });
  };

  const getVideoId = (url: string) => {
    const match = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
    return match ? match[1] : null;
  };

  const videoId = watchedUrl ? getVideoId(watchedUrl) : null;

  return (
    <div className={className}>
      <Card className="max-w-4xl mx-auto">
        <div className="p-6">
          <h1 className="text-3xl font-bold text-center mb-8">YouTube视频分析工具</h1>
          
          <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
            <div>
              <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
                YouTube视频链接
              </label>
              <input
                {...register('url')}
                type="url"
                placeholder="粘贴YouTube视频链接..."
                disabled={isLoading}
                className={`input text-lg ${errors.url ? 'border-red-500' : ''}`}
              />
              {errors.url && (
                <p className="mt-1 text-sm text-red-600">{errors.url.message}</p>
              )}
              
              {videoId && (
                <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <img
                      src={`https://img.youtube.com/vi/${videoId}/mqdefault.jpg`}
                      alt="视频缩略图"
                      className="w-20 h-15 object-cover rounded"
                    />
                    <div>
                      <p className="text-sm text-gray-600">视频ID: {videoId}</p>
                      <p className="text-xs text-gray-500">缩略图预览</p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <AnalysisTypeSelector
              selectedType={selectedType}
              onTypeChange={handleTypeChange}
            />

            <div className="border-t pt-6">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="mb-4"
              >
                {showAdvanced ? '隐藏' : '显示'}高级选项
              </Button>

              {showAdvanced && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      最大评论数量
                    </label>
                    <input
                      {...register('maxComments', { valueAsNumber: true })}
                      type="number"
                      min="10"
                      max="1000"
                      placeholder="100"
                      disabled={isLoading}
                      className="input w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      语言设置
                    </label>
                    <select
                      {...register('language')}
                      className="input w-full"
                      disabled={isLoading}
                    >
                      <option value="zh-CN">中文</option>
                      <option value="en-US">English</option>
                      <option value="ja-JP">日本語</option>
                      <option value="ko-KR">한국어</option>
                    </select>
                  </div>

                  <div className="md:col-span-2">
                    <label className="flex items-center space-x-2">
                      <input
                        {...register('enableTranscription')}
                        type="checkbox"
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        disabled={isLoading}
                      />
                      <span className="text-sm text-gray-700">启用音频转录</span>
                    </label>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-center pt-6">
              <Button
                type="submit"
                size="lg"
                loading={isLoading}
                disabled={!isValid || isLoading}
                className="px-8 py-3 text-lg"
              >
                {isLoading ? '正在分析...' : '开始分析'}
              </Button>
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
};
