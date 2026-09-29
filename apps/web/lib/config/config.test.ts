import { mkdtempSync, writeFileSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { assertProductionConfig, loadPricing, resolveConfigDir } from "@/lib/config";

describe("config loader", () => {
  it("finds the repo config directory", () => {
    const dir = resolveConfigDir();
    expect(dir.endsWith(`${path.sep}config`)).toBe(true);
    const pricing = loadPricing(dir);
    expect(pricing.currency).toBe("BRL");
    expect(pricing.tiers.length).toBeGreaterThan(0);
  });

  it("refuses production boot when a tier is still R$ 0", () => {
    const dir = mkdtempSync(path.join(os.tmpdir(), "parecer-config-"));
    writeFileSync(
      path.join(dir, "pricing.json"),
      JSON.stringify({
        currency: "BRL",
        tiers: [{ id: "curto", maxWords: 40000, priceCents: 0 }],
      }),
    );
    writeFileSync(
      path.join(dir, "consents.json"),
      JSON.stringify({
        bookxpress: {
          relationship: "propria",
          legalName: "Bookxpress",
          cnpj: "00.000.000/0001-00",
          contactEmail: "contato@example.com",
          currentVersion: "bookxpress-v1",
          versions: {
            "bookxpress-v1": { label: "label", details: "details" },
          },
          proofRetentionYears: 5,
        },
      }),
    );

    expect(() =>
      assertProductionConfig({ NODE_ENV: "production" } as NodeJS.ProcessEnv, dir),
    ).toThrow(/priceCents=0/);
  });

  it("skips production checks outside production", () => {
    expect(() => assertProductionConfig({ NODE_ENV: "development" })).not.toThrow();
  });
});
