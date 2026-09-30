import { describe, expect, it } from "vitest";
import { maxUploadMb } from "@/lib/config";
import { sellerIdentification } from "@/lib/seller/identification";
import { demoChaptersDetected, isAcceptedManuscript } from "@/lib/uploads/rules";

describe("sellerIdentification", () => {
  it("shows a pending CNPJ when the config is still empty", () => {
    expect(
      sellerIdentification({
        displayName: "Parecer Literário",
        legalName: "",
        cnpj: "",
        contactEmail: "contato@seudominio.com.br",
        address: "",
      }),
    ).toEqual(["Parecer Literário", "CNPJ ainda não informado"]);
  });
});

describe("upload rules", () => {
  it("accepts the manuscript extensions and flags the demo chapter failure", () => {
    expect(isAcceptedManuscript("conto.txt")).toBe(true);
    expect(isAcceptedManuscript("foto.png")).toBe(false);
    expect(demoChaptersDetected("sem-capitulos.txt")).toBe(false);
    expect(demoChaptersDetected("conto.txt")).toBe(true);
  });

  it("falls back to 20 MB when the env var is absent", () => {
    expect(maxUploadMb({} as NodeJS.ProcessEnv)).toBe(20);
  });
});
