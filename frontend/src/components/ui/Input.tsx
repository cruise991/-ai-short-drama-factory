import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  leftIcon,
  className = '',
  id,
  ...props
}) => {
  const inputId = id || (label ? `input_${label.replace(/\s+/g, '_').toLowerCase()}` : undefined);

  return (
    <div className="w-full flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-xs font-medium text-gray-300">
          {label}
        </label>
      )}
      <div className="relative flex items-center">
        {leftIcon && (
          <div className="absolute left-3 text-gray-400 pointer-events-none flex items-center">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          className={`w-full bg-gray-900/80 border ${
            error ? 'border-red-500/70 focus:border-red-500' : 'border-gray-700/80 focus:border-indigo-500'
          } rounded-lg px-3.5 py-2 text-sm text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all ${
            leftIcon ? 'pl-9' : ''
          } ${className}`}
          {...props}
        />
      </div>
      {error && <span className="text-xs text-red-400">{error}</span>}
    </div>
  );
};
