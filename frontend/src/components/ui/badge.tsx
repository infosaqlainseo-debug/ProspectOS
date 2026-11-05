import React from "react";

export type BadgeVariant = "default" | "secondary" | "success" | "warning" | "destructive" | "ai" | "outline" | "neutral";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: "sm" | "md";
  dot?: boolean;
}

export function Badge({
  children,
  variant = "default",
  size = "sm",
  dot = false,
  className = "",
  ...props
}: BadgeProps) {
  const variantStyles: Record<BadgeVariant, string> = {
    default: "bg-blue-50 text-blue-700 border-blue-200/60",
    secondary: "bg-slate-100 text-slate-700 border-slate-200",
    success: "bg-emerald-50 text-emerald-700 border-emerald-200/60",
    warning: "bg-amber-50 text-amber-700 border-amber-200/60",
    destructive: "bg-rose-50 text-rose-700 border-rose-200/60",
    ai: "bg-indigo-50 text-indigo-700 border-indigo-200/60",
    outline: "bg-white text-slate-700 border-slate-300",
    neutral: "bg-slate-50 text-slate-600 border-slate-200",
  };

  const dotColors: Record<BadgeVariant, string> = {
    default: "bg-blue-500",
    secondary: "bg-slate-400",
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    destructive: "bg-rose-500",
    ai: "bg-indigo-500",
    outline: "bg-slate-400",
    neutral: "bg-slate-400",
  };

  const sizeStyles = size === "sm" ? "px-2 py-0.5 text-[11px] font-medium" : "px-2.5 py-1 text-xs font-semibold";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border tracking-tight transition-colors ${variantStyles[variant]} ${sizeStyles} ${className}`}
      {...props}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
}

