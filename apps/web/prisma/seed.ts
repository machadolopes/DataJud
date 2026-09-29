import { prisma } from "../lib/db";

async function main() {
  const orderCount = await prisma.order.count();
  console.log(
    JSON.stringify({
      ok: true,
      message:
        "F0 seed is a no-op. Example orders in several statuses arrive in a later phase (pnpm seed).",
      orderCount,
    }),
  );
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
