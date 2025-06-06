'use client';

import React from 'react';
import { BaseComponentProps } from '../types/ui';

interface LoadingSpinnerProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'white';
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  variant = 'primary',
  text,
  className = '',
  testId
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const variantClasses = {
    primary: 'text-primary-600',
    secondary: 'text-gray-600',
    white: 'text-white'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  };

  return (
    <div 
      className={`flex items-center justify-center ${className}`}
      data-testid={testId}
    >
      <div className="flex items-center space-x-3">
        <div
          className={`animate-spin rounded-full border-2 border-transparent border-t-current ${sizeClasses[size]} ${variantClasses[variant]}`}
          role="status"
          aria-label="加载中"
        />
        {text && (
          <span className={`${textSizeClasses[size]} ${variantClasses[variant]} font-medium`}>
            {text}
          </span>
        )}
      </div>
    </div>
  );
};

export default LoadingSpinner;
