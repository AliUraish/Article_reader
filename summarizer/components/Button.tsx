
import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  isLoading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'primary', 
  isLoading, 
  className, 
  ...props 
}) => {
  const baseStyles = "px-6 py-3 font-medium transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-orange-600 hover:bg-orange-500 text-white shadow-lg shadow-orange-900/10",
    secondary: "bg-[#E0DCD6] hover:bg-[#D5D1CB] text-[#101010]",
    outline: "border border-orange-600 text-orange-600 hover:bg-orange-50"
  };

  return (
    <button 
      className={`${baseStyles} ${variants[variant]} ${className}`}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? (
        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
      ) : null}
      {children}
    </button>
  );
};
