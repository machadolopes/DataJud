export function formatCents(cents: number, currency: string): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency,
  }).format(cents / 100);
}

export function formatInteger(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function equivalentPages(wordCount: number, wordsPerPage: number): number {
  return Math.round(wordCount / wordsPerPage);
}

export function formatBytes(bytes: number): string {
  const format = (value: number) =>
    new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(value);
  if (bytes < 1024) {
    return `${format(bytes)} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${format(bytes / 1024)} KB`;
  }
  return `${format(bytes / (1024 * 1024))} MB`;
}

export function formatCountdown(totalSeconds: number): string {
  const safe = Math.max(0, totalSeconds);
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function maskCpf(value: string): string {
  const digits = value.replace(/\D/g, "").slice(0, 11);
  const part1 = digits.slice(0, 3);
  const part2 = digits.slice(3, 6);
  const part3 = digits.slice(6, 9);
  const part4 = digits.slice(9, 11);
  if (digits.length <= 3) return part1;
  if (digits.length <= 6) return `${part1}.${part2}`;
  if (digits.length <= 9) return `${part1}.${part2}.${part3}`;
  return `${part1}.${part2}.${part3}-${part4}`;
}
