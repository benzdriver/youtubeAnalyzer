'use client';

import React from 'react';
import { Card } from './ui';
import { LoadingSpinner } from './LoadingSpinner';
import { BaseComponentProps } from '../types/ui';

interface LoadingStateProps extends BaseComponentProps {
  title?: string;
  description?: string;
  variant?: 'card' | 'inline' | 'fullscreen';
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  title = '加载中...',
  description,
  variant = 'card',
  size = 'md',
  className = '',
  testId
}) => {
  const content = (
    <div className="text-center">
      <LoadingSpinner size={size} text={title} />
      {description && (
        <p className="mt-4 text-sm text-gray-600">
          {description}
        </p>
      )}
    </div>
  );

  if (variant === 'fullscreen') {
    return (
      <div 
        className={`fixed inset-0 bg-white bg-opacity-90 flex items-center justify-center z-50 ${className}`}
        data-testid={testId}
      >
        {content}
      </div>
    );
  }

  if (variant === 'inline') {
    return (
      <div 
        className={`py-8 ${className}`}
        data-testid={testId}
      >
        {content}
      </div>
    );
  }

  return (
    <Card className={`p-8 ${className}`} testId={testId}>
      {content}
    </Card>
  );
};

export default LoadingState;
