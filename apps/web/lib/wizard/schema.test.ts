import { describe, expect, it } from "vitest";
import { emptyWorkForm, workSchema } from "@/lib/wizard/schema";

const valid = {
  name: "Ana Lima",
  email: "ana@example.com",
  emailConfirm: "Ana@example.com",
  cpf: "529.982.247-25",
  title: "O rio",
  genre: "romance",
  audience: "adulto",
  acceptTerms: true,
  acceptAi: true,
  bookxpressOptIn: false,
};

describe("workSchema", () => {
  it("starts with the Bookxpress box unchecked", () => {
    expect(emptyWorkForm().bookxpressOptIn).toBe(false);
    expect(emptyWorkForm().acceptTerms).toBe(false);
  });

  it("accepts a complete form and keeps the optional consent false", () => {
    const parsed = workSchema.parse(valid);
    expect(parsed.bookxpressOptIn).toBe(false);
    expect(parsed.email).toBe("ana@example.com");
  });

  it("rejects mismatched e-mails, invalid CPF and missing required consents", () => {
    const result = workSchema.safeParse({
      ...valid,
      emailConfirm: "outra@example.com",
      cpf: "111.111.111-11",
      acceptTerms: false,
      acceptAi: false,
    });
    expect(result.success).toBe(false);
    if (!result.success) {
      const paths = result.error.issues.map((issue) => issue.path[0]);
      expect(paths).toContain("emailConfirm");
      expect(paths).toContain("cpf");
      expect(paths).toContain("acceptTerms");
      expect(paths).toContain("acceptAi");
    }
  });
});
