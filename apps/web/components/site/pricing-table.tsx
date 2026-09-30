import type { PricingConfig } from "@/lib/config";
import { formatCents } from "@/lib/format";

export function PricingTable({
  pricing,
  pricesUnpublished,
}: {
  pricing: PricingConfig;
  pricesUnpublished: boolean;
}) {
  return (
    <div>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {pricing.tiers.map((tier) => (
          <li key={tier.id} className="flex flex-col border border-line p-5">
            <h3 className="text-[22px]">{tier.label ?? tier.id}</h3>
            <p className="mt-6 font-serif text-[30px] leading-none">
              {formatCents(tier.priceCents, pricing.currency)}
            </p>
          </li>
        ))}
      </ul>
      {pricesUnpublished ? (
        <p className="measure mt-6 text-[16px] leading-[1.6]">
          Os valores acima estão zerados na configuração de exemplo. Os preços de lançamento entram
          nesta tabela antes de abrirmos os pedidos.
        </p>
      ) : null}
    </div>
  );
}
