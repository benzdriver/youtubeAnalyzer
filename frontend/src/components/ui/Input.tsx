import React, { forwardRef } from 'react';
import { InputProps } from '@/types/ui';

const Input = forwardRef<HTMLInputElement, InputProps & React.InputHTMLAttributes<HTMLInputElement>>(({
  type = 'text',
  placeholder,
  value,
  defaultValue,
  disabled = false,
  required = false,
  error,
  min,
  max,
  onChange,
  onBlur,
  onFocus,
  className = '',
  testId,
  ...props
}, ref) => {
  const baseClasses = 'block w-full rounded-lg border px-3 py-2 text-base placeholder-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const stateClasses = error
    ? 'border-red-500 focus:border-red-500 focus:ring-red-500'
    : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500';
    
  const disabledClasses = disabled
    ? 'bg-gray-50 cursor-not-allowed'
    : 'bg-white hover:border-gray-400';

  const classes = `${baseClasses} ${stateClasses} ${disabledClasses} ${className}`;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onChange) {
      onChange(e.target.value);
    }
  };

  return (
    <div className="w-full">
      <input
        ref={ref}
        type={type}
        placeholder={placeholder}
        value={value}
        defaultValue={defaultValue}
        disabled={disabled}
        required={required}
        min={min}
        max={max}
        onChange={handleChange}
        onBlur={onBlur}
        onFocus={onFocus}
        className={classes}
        data-testid={testId}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input;
