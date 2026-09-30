import * as React from "react";
import { cn } from "@/lib/utils";

function Input({ className, type = "text", ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "h-11 w-full rounded-[6px] border border-line bg-paper px-3 text-[16px] leading-normal text-ink placeholder:text-muted disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
