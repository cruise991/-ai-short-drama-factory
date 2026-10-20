import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  interactive?: boolean;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  children,
  interactive = false,
  className = '',
  ...props
}) => {
  const base = interactive ? 'glass-panel-interactive cursor-pointer' : 'glass-panel';
  return (
    <div className={`${base} p-5 ${className}`} {...props}>
      {children}
    </div>
  );
};
