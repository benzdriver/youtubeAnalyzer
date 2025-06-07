'use client';

import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  onClick?: () => void;
  onKeyDown?: (e: React.KeyboardEvent) => void;
  tabIndex?: number;
  role?: string;
  'aria-pressed'?: boolean;
  'aria-label'?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  className = '',
  onClick,
  onKeyDown,
  tabIndex,
  role,
  'aria-pressed': ariaPressed,
  'aria-label': ariaLabel
}) => {
  const baseClasses = 'inline-flex items-center font-medium rounded-full transition-colors';
  
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-2 text-base'
  };

  const variantClasses = {
    primary: 'bg-blue-100 text-blue-800 border border-blue-200',
    secondary: 'bg-gray-100 text-gray-800 border border-gray-200',
    success: 'bg-green-100 text-green-800 border border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
    error: 'bg-red-100 text-red-800 border border-red-200',
    outline: 'bg-transparent text-gray-700 border border-gray-300'
  };

  const hoverClasses = onClick ? {
    primary: 'hover:bg-blue-200 cursor-pointer',
    secondary: 'hover:bg-gray-200 cursor-pointer',
    success: 'hover:bg-green-200 cursor-pointer',
    warning: 'hover:bg-yellow-200 cursor-pointer',
    error: 'hover:bg-red-200 cursor-pointer',
    outline: 'hover:bg-gray-50 cursor-pointer'
  } : {};

  const classes = `
    ${baseClasses}
    ${sizeClasses[size]}
    ${variantClasses[variant]}
    ${onClick ? hoverClasses[variant] : ''}
    ${className}
  `.trim();

  if (onClick) {
    return (
      <button
        onClick={onClick}
        onKeyDown={onKeyDown}
        className={classes}
        type="button"
        tabIndex={tabIndex}
        role={role}
        aria-pressed={ariaPressed}
        aria-label={ariaLabel}
      >
        {children}
      </button>
    );
  }

  return (
    <span className={classes}>
      {children}
    </span>
  );
};

export default Badge;
