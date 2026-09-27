interface FieldProps {
  label: string;
  children: React.ReactNode;
}

export function Field({ label, children }: FieldProps) {
  return (
    <label className="block space-y-1">
      <span className="text-sm font-medium text-zinc-600">{label}</span>
      {children}
    </label>
  );
}
