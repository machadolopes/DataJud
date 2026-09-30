/**
 * Fixed figures for the F1 wizard. Real word counts arrive with the ingest job (F2).
 * The tier and price are still resolved from config/pricing.json, never typed here.
 */
export const DEMO_ANALYSIS = {
  wordCount: 68420,
  chapterCount: 18,
} as const;

export const DEMO_ORDER = {
  publicId: "demo",
  accessToken: "demonstracao",
} as const;

/** Not a payable Pix payload. Shown only in the demonstration step. */
export const DEMO_PIX_CODE = "DEMO-PARECER-LITERARIO-NAO-E-UM-PIX-REAL";

export const DEMO_MANUSCRIPT_NAME = "manuscrito-de-demonstracao.txt";
