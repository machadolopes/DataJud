import { z } from "zod";
import { loadPricing, type PricingConfig } from "@/lib/config";

const wordCountSchema = z.number().int().positive();

export type PriceQuote = {
  tierId: string;
  label: string;
  maxWords: number;
  priceCents: number;
  currency: string;
};

export class PricingError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "PricingError";
  }
}

export function priceForWordCount(
  wordCount: number,
  pricing: PricingConfig = loadPricing(),
): PriceQuote {
  const words = wordCountSchema.parse(wordCount);
  const sorted = [...pricing.tiers].sort((a, b) => a.maxWords - b.maxWords);
  const tier = sorted.find((candidate) => words <= candidate.maxWords);
  if (!tier) {
    const max = sorted.at(-1)?.maxWords ?? 0;
    throw new PricingError(`Word count ${words} exceeds the maximum configured tier (${max}).`);
  }
  return {
    tierId: tier.id,
    label: tier.label ?? tier.id,
    maxWords: tier.maxWords,
    priceCents: tier.priceCents,
    currency: pricing.currency,
  };
}
