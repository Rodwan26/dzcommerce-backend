import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  helperText?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, id, leftIcon, rightIcon, helperText, ...props }, ref) => {
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={id} className="label">{label}</label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-[rgb(var(--color-text-secondary))]">{leftIcon}</div>
          )}
          <input
            ref={ref}
            id={id}
            className={cn(
              "w-full px-3.5 py-2.5 bg-[rgb(var(--color-surface))] border border-[rgb(var(--color-border))] rounded-lg font-body text-sm text-[rgb(var(--color-text))] placeholder:text-[rgb(var(--color-text-secondary))]/50 transition-all duration-150",
              "focus:outline-none focus:border-[rgb(var(--color-accent))] focus:shadow-[0_0_0_3px_rgba(58,95,132,0.12)]",
              error && "border-[rgb(var(--color-danger))] focus:border-[rgb(var(--color-danger))] focus:shadow-[0_0_0_3px_rgba(190,60,45,0.12)]",
              !!leftIcon && "pr-10",
              !!rightIcon && "pl-10",
              className
            )}
            {...props}
          />
          {rightIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[rgb(var(--color-text-secondary))]">{rightIcon}</div>
          )}
        </div>
        {error && <p className="text-xs text-[rgb(var(--color-danger))]">{error}</p>}
        {helperText && !error && <p className="text-xs text-[rgb(var(--color-text-secondary))]">{helperText}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
