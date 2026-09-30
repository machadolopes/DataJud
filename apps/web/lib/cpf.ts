export function cpfDigits(value: string): string {
  return value.replace(/\D/g, "");
}

export function isValidCpf(value: string): boolean {
  const digits = cpfDigits(value);
  if (digits.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(digits)) return false;

  const checkDigit = (base: string, factor: number) => {
    let sum = 0;
    for (const char of base) {
      sum += Number(char) * factor;
      factor -= 1;
    }
    const rest = (sum * 10) % 11;
    return rest === 10 ? 0 : rest;
  };

  const first = checkDigit(digits.slice(0, 9), 10);
  const second = checkDigit(digits.slice(0, 10), 11);
  return first === Number(digits[9]) && second === Number(digits[10]);
}
