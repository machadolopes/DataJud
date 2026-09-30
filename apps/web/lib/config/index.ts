import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { z } from "zod";

const pricingSchema = z.object({
  currency: z.string().min(1),
  tiers: z
    .array(
      z.object({
        id: z.string().min(1),
        label: z.string().optional(),
        maxWords: z.number().int().positive(),
        priceCents: z.number().int().nonnegative(),
      }),
    )
    .min(1),
});

const consentVersionSchema = z.object({
  label: z.string().min(1),
  details: z.string().min(1),
});

const consentsSchema = z.object({
  bookxpress: z.object({
    relationship: z.enum(["propria", "parceira"]),
    legalName: z.string(),
    cnpj: z.string(),
    contactEmail: z.string(),
    currentVersion: z.string().min(1),
    versions: z.record(consentVersionSchema),
    proofRetentionYears: z.number().int().positive(),
  }),
});

const sellerSchema = z.object({
  seller: z.object({
    displayName: z.string().min(1),
    legalName: z.string(),
    cnpj: z.string(),
    contactEmail: z.string().min(1),
    address: z.string(),
  }),
});

const limitsSchema = z.object({
  quoteValidityHours: z.number().positive(),
  pixExpirationMinutes: z.number().int().positive(),
  wordsPerPage: z.number().int().positive(),
  downloadUrlMinutes: z.number().int().positive(),
});

const retentionSchema = z.object({
  manuscriptDaysAfterDelivery: z.number().int().positive(),
  workArtifactsDaysAfterDelivery: z.number().int().positive(),
  reportDaysAfterDelivery: z.number().int().positive(),
  consentProofYearsAfterRevocation: z.number().int().positive(),
});

export type PricingConfig = z.infer<typeof pricingSchema>;
export type ConsentsConfig = z.infer<typeof consentsSchema>;
export type SellerConfig = z.infer<typeof sellerSchema>["seller"];
export type LimitsConfig = z.infer<typeof limitsSchema>;
export type RetentionConfig = z.infer<typeof retentionSchema>;

/** Spec default when MAX_UPLOAD_MB is unset. Matches .env.example. */
export const DEFAULT_MAX_UPLOAD_MB = 20;

export function resolveConfigDir(cwd = process.cwd()): string {
  const candidates = [path.resolve(cwd, "config"), path.resolve(cwd, "../../config")];
  for (const dir of candidates) {
    if (existsSync(path.join(dir, "pricing.json"))) {
      return dir;
    }
  }
  throw new Error("config directory not found (expected config/pricing.json)");
}

function readJson(filePath: string): unknown {
  return JSON.parse(readFileSync(filePath, "utf8"));
}

export function loadPricing(configDir = resolveConfigDir()): PricingConfig {
  return pricingSchema.parse(readJson(path.join(configDir, "pricing.json")));
}

export function loadConsents(configDir = resolveConfigDir()): ConsentsConfig {
  return consentsSchema.parse(readJson(path.join(configDir, "consents.json")));
}

export function loadSeller(configDir = resolveConfigDir()) {
  return sellerSchema.parse(readJson(path.join(configDir, "seller.json")));
}

export function loadLimits(configDir = resolveConfigDir()): LimitsConfig {
  return limitsSchema.parse(readJson(path.join(configDir, "limits.json")));
}

export function loadRetention(configDir = resolveConfigDir()): RetentionConfig {
  return retentionSchema.parse(readJson(path.join(configDir, "retention.json")));
}

export function maxUploadMb(env: NodeJS.ProcessEnv = process.env): number {
  const raw = env.MAX_UPLOAD_MB;
  if (raw === undefined || raw.trim() === "") {
    return DEFAULT_MAX_UPLOAD_MB;
  }
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error("MAX_UPLOAD_MB must be a positive integer.");
  }
  return value;
}

export function assertProductionConfig(
  env: NodeJS.ProcessEnv = process.env,
  configDir = resolveConfigDir(),
): void {
  if (env.NODE_ENV !== "production") {
    return;
  }

  const pricing = loadPricing(configDir);
  const zeroTier = pricing.tiers.find((tier) => tier.priceCents === 0);
  if (zeroTier) {
    throw new Error(
      `Production refused to start: pricing tier "${zeroTier.id}" has priceCents=0. Set real prices in config/pricing.json.`,
    );
  }

  const consents = loadConsents(configDir);
  if (!consents.bookxpress.legalName.trim() || !consents.bookxpress.contactEmail.trim()) {
    throw new Error(
      "Production refused to start: config/consents.json bookxpress.legalName and contactEmail must be set.",
    );
  }

  const current = consents.bookxpress.versions[consents.bookxpress.currentVersion];
  if (!current) {
    throw new Error(
      `Production refused to start: consents currentVersion "${consents.bookxpress.currentVersion}" is missing from versions.`,
    );
  }
}
