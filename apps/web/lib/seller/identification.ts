import type { SellerConfig } from "@/lib/config";

export function sellerIdentification(seller: SellerConfig): string[] {
  const lines = [seller.legalName.trim() || seller.displayName];
  const cnpj = seller.cnpj.trim();
  lines.push(cnpj ? `CNPJ ${cnpj}` : "CNPJ ainda não informado");
  const address = seller.address.trim();
  if (address) lines.push(address);
  return lines;
}
