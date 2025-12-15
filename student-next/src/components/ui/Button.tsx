"use client";

import Link from "next/link";
import { ButtonHTMLAttributes, AnchorHTMLAttributes } from "react";
import { twMerge } from "tailwind-merge";

type Variant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  AnchorHTMLAttributes<HTMLAnchorElement> & {
    variant?: Variant;
    href?: string;
    fullWidth?: boolean;
  };

const variantClasses: Record<Variant, string> = {
  primary: "bg-slate-900 text-white hover:bg-slate-800",
  secondary: "bg-[#e5e5e5] text-slate-900 hover:bg-[#d8d8d8]",
  ghost: "bg-transparent text-slate-700 hover:bg-slate-200",
};

export function Button({ variant = "secondary", className, fullWidth, href, children, ...props }: ButtonProps) {
  const classes = twMerge(
    "inline-flex items-center justify-center rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold transition",
    variantClasses[variant],
    fullWidth && "w-full",
    className
  );

  if (href) {
    return (
      <Link href={href} className={classes} {...(props as AnchorHTMLAttributes<HTMLAnchorElement>)}>
        {children}
      </Link>
    );
  }

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}

export default Button;
