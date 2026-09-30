import { describe, expect, it } from "vitest";
import { equivalentPages, formatCents, formatCountdown } from "@/lib/format";
import { priceForWordCount } from "@/lib/pricing";
import { DEMO_ANALYSIS } from "@/lib/demo/fixture";
import type { PricingConfig } from "@/lib/config";

describe("format", () => {
  it("formats cents in pt-BR", () => {
    expect(formatCents(12345, "BRL").replace(/\u00a0/g, " ")).toBe("R$ 123,45");
  });

  it("rounds equivalent pages from the configured divisor", () => {
    expect(equivalentPages(DEMO_ANALYSIS.wordCount, 350)).toBe(195);
  });

  it("formats the pix countdown", () => {
    expect(formatCountdown(30 * 60)).toBe("30:00");
    expect(formatCountdown(0)).toBe("00:00");
  });
});

describe("demo quote", () => {
  it("lands in the middle tier when prices come from config", () => {
    const pricing: PricingConfig = {
      currency: "BRL",
      tiers: [
        { id: "curto", label: "Curto", maxWords: 40000, priceCents: 100 },
        { id: "medio", label: "Médio", maxWords: 90000, priceCents: 200 },
        { id: "longo", label: "Longo", maxWords: 150000, priceCents: 300 },
      ],
    };
    expect(priceForWordCount(DEMO_ANALYSIS.wordCount, pricing).tierId).toBe("medio");
  });
});
