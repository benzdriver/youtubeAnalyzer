import React from 'react';
import { CardProps } from '@/types/ui';

const Card: React.FC<CardProps & { onClick?: () => void }> = ({
  children,
  title,
  subtitle,
  padding = 'md',
  shadow = 'md',
  border = true,
  className = '',
  testId,
  onClick,
  ...props
}) => {
  const baseClasses = 'bg-white rounded-lg';
  
  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  };

  const shadowClasses = {
    none: '',
    sm: 'shadow-sm',
    md: 'shadow-md',
    lg: 'shadow-lg'
  };

  const borderClasses = border ? 'border border-gray-200' : '';

  const classes = `${baseClasses} ${paddingClasses[padding]} ${shadowClasses[shadow]} ${borderClasses} ${className}`;

  return (
    <div className={classes} data-testid={testId} onClick={onClick} {...props}>
      {(title || subtitle) && (
        <div className={`${padding !== 'none' ? 'mb-4' : ''}`}>
          {title && (
            <h3 className="text-lg font-semibold text-gray-900">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-sm text-gray-600 mt-1">
              {subtitle}
            </p>
          )}
        </div>
      )}
      {children}
    </div>
  );
};

export default Card;
