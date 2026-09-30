import type { ReactNode } from "react";

export function DemoNotice({ children }: { children: ReactNode }) {
  return <p className="border border-line px-4 py-3 text-[16px] leading-snug">{children}</p>;
}
