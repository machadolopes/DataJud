import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-[6px] border px-5 py-2 text-[16px] leading-none font-medium transition-colors duration-200 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "border-accent bg-accent text-accent-ink hover:bg-accent/90",
        outline: "border-ink bg-transparent text-ink hover:bg-ink/5",
      },
    },
    defaultVariants: {
      variant: "primary",
    },
  },
);

function Button({
  className,
  variant,
  asChild = false,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  }) {
  const Comp = asChild ? Slot : "button";
  return (
    <Comp data-slot="button" className={cn(buttonVariants({ variant }), className)} {...props} />
  );
}

export { Button, buttonVariants };
