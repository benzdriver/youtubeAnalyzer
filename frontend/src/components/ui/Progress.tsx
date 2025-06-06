import React from 'react';
import { ProgressProps } from '@/types/ui';

const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  size = 'md',
  variant = 'default',
  showLabel = false,
  label,
  className = '',
  testId,
  ...props
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  
  const sizeClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4'
  };

  const variantClasses = {
    default: 'bg-blue-600',
    success: 'bg-green-600',
    warning: 'bg-yellow-600',
    error: 'bg-red-600'
  };

  const containerClasses = `w-full bg-gray-200 rounded-full overflow-hidden ${sizeClasses[size]} ${className}`;
  const barClasses = `h-full transition-all duration-300 ease-out ${variantClasses[variant]}`;

  return (
    <div data-testid={testId} {...props}>
      {showLabel && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">
            {label || '进度'}
          </span>
          <span className="text-sm text-gray-600">
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className={containerClasses}>
        <div
          className={barClasses}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={max}
          aria-label={label || `进度: ${Math.round(percentage)}%`}
        />
      </div>
    </div>
  );
};

export default Progress;
