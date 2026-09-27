interface BadgeProps {
  color?: 'green' | 'amber' | 'red' | 'gray';
  className?: string;
  children: React.ReactNode;
}

const COLOR_CLASSES = {
  green: 'bg-emerald-100 text-emerald-800',
  amber: 'bg-amber-100 text-amber-800',
  red: 'bg-red-100 text-red-800',
  gray: 'bg-zinc-100 text-zinc-700',
};

export function Badge({ color = 'gray', className = '', children }: BadgeProps) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${COLOR_CLASSES[color]} ${className}`}>
      {children}
    </span>
  );
}
