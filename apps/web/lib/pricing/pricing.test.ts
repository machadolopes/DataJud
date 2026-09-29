import { describe, expect, it } from "vitest";
import { priceForWordCount, PricingError } from "@/lib/pricing";
import type { PricingConfig } from "@/lib/config";

const pricing: PricingConfig = {
  currency: "BRL",
  tiers: [
    { id: "curto", label: "Curto", maxWords: 40000, priceCents: 10000 },
    { id: "medio", label: "Médio", maxWords: 90000, priceCents: 20000 },
    { id: "longo", label: "Longo", maxWords: 150000, priceCents: 30000 },
    { id: "extenso", label: "Extenso", maxWords: 200000, priceCents: 40000 },
  ],
};

describe("priceForWordCount", () => {
  it("selects the first tier that covers the word count", () => {
    expect(priceForWordCount(1, pricing).tierId).toBe("curto");
    expect(priceForWordCount(40000, pricing).tierId).toBe("curto");
    expect(priceForWordCount(40001, pricing).tierId).toBe("medio");
    expect(priceForWordCount(200000, pricing).tierId).toBe("extenso");
  });

  it("never takes a monetary value from the caller", () => {
    const quote = priceForWordCount(10000, pricing);
    expect(quote.priceCents).toBe(10000);
    expect(quote.currency).toBe("BRL");
  });

  it("rejects word counts above the last tier", () => {
    expect(() => priceForWordCount(200001, pricing)).toThrow(PricingError);
  });
});
