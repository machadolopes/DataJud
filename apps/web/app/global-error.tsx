"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <h1>Algo deu errado</h1>
        <p>{error.message}</p>
        <button type="button" onClick={() => reset()}>
          Tentar de novo
        </button>
      </body>
    </html>
  );
}
