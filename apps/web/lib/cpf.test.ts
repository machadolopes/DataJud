import { describe, expect, it } from "vitest";
import { isValidCpf } from "@/lib/cpf";
import { maskCpf } from "@/lib/format";

describe("cpf", () => {
  it("accepts a valid CPF and rejects the obvious fakes", () => {
    expect(isValidCpf("529.982.247-25")).toBe(true);
    expect(isValidCpf("52998224725")).toBe(true);
    expect(isValidCpf("111.111.111-11")).toBe(false);
    expect(isValidCpf("529.982.247-26")).toBe(false);
    expect(isValidCpf("123")).toBe(false);
  });

  it("masks digits as the author types", () => {
    expect(maskCpf("52998224725")).toBe("529.982.247-25");
    expect(maskCpf("529")).toBe("529");
  });
});
