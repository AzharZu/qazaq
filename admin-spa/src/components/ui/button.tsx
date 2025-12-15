import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "../../utils/cn";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "destructive" | "outline";
  size?: "sm" | "md";
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => {
    const styles = {
      primary: "bg-primary text-white hover:bg-blue-600 border border-blue-600",
      ghost: "bg-transparent border border-transparent hover:border-border text-gray-800",
      destructive: "bg-destructive text-white hover:bg-red-600 border border-red-600",
      outline: "bg-white border border-border text-gray-900 hover:bg-gray-50",
    }[variant];
    const sizes = size === "sm" ? "px-3 py-1.5 text-sm" : "px-4 py-2";
    return (
      <button
        ref={ref}
        className={cn("rounded-md font-semibold transition-colors disabled:opacity-60", styles, sizes, className)}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
