"use client";

import Link from "next/link";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";

type BookxpressOptInProps = {
  label: string;
  details: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
};

/**
 * Optional marketing consent. Callers must pass checked={false} on first render.
 * This control does not look up the author's e-mail.
 */
export function BookxpressOptIn({
  label,
  details,
  checked,
  onCheckedChange,
}: BookxpressOptInProps) {
  return (
    <div className="mt-8 border-t border-line pt-6">
      <p className="text-[16px] leading-snug">
        Opcional. Não muda o preço nem a análise do manuscrito.
      </p>
      <div className="mt-4 flex items-start gap-3">
        <Checkbox
          id="bookxpress-opt-in"
          checked={checked}
          onCheckedChange={(value) => onCheckedChange(value === true)}
          aria-describedby="bookxpress-details"
        />
        <Label htmlFor="bookxpress-opt-in" className="cursor-pointer">
          {label}
        </Label>
      </div>
      <details className="mt-3">
        <summary className="cursor-pointer text-[16px] underline decoration-line underline-offset-4">
          Saiba mais
        </summary>
        <div id="bookxpress-details" className="measure mt-3 space-y-3 text-[16px] leading-[1.6]">
          <p>{details}</p>
          <p>
            <Link
              href="/privacidade#bookxpress"
              className="underline decoration-line underline-offset-4"
            >
              Ler na política de privacidade
            </Link>
          </p>
        </div>
      </details>
    </div>
  );
}
