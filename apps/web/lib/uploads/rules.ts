export const MANUSCRIPT_EXTENSIONS = [".docx", ".pdf", ".epub", ".txt"] as const;

export type ManuscriptExtension = (typeof MANUSCRIPT_EXTENSIONS)[number];

export function manuscriptExtension(filename: string): string {
  const dot = filename.lastIndexOf(".");
  if (dot <= 0) return "";
  return filename.slice(dot).toLowerCase();
}

export function isAcceptedManuscript(filename: string): boolean {
  return (MANUSCRIPT_EXTENSIONS as readonly string[]).includes(manuscriptExtension(filename));
}

/** Demo-only signal so the quote step can show the missing-chapters warning. */
export function demoChaptersDetected(filename: string): boolean {
  return !filename.toLowerCase().includes("sem-capitulos");
}

export function maxUploadBytes(maxUploadMb: number): number {
  return maxUploadMb * 1024 * 1024;
}
