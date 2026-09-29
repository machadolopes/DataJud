export async function register() {
  if (process.env.NEXT_RUNTIME === "edge") {
    return;
  }
  if (process.env.NEXT_PHASE === "phase-production-build") {
    return;
  }
  const { assertProductionConfig } = await import("@/lib/config");
  assertProductionConfig();
}
