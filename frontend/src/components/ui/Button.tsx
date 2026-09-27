import { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'solid' | 'ghost';
}

const SIZE_CLASSES = { sm: 'px-2 py-1 text-sm', md: 'px-4 py-2', lg: 'px-6 py-3 text-lg' };
const VARIANT_CLASSES = {
  solid: 'bg-blue-600 text-white hover:bg-blue-700',
  ghost: 'bg-transparent text-zinc-300 hover:bg-zinc-800',
};

export function Button({ size = 'md', variant = 'solid', className = '', ...props }: ButtonProps) {
  return (
    <button
      className={`rounded font-medium disabled:opacity-50 ${SIZE_CLASSES[size]} ${VARIANT_CLASSES[variant]} ${className}`}
      {...props}
    />
  );
}
