"use client";

import "./globals.css";

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="pt-BR">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          background: "#FAF8F3",
          color: "#1C1B19",
          fontFamily: "Georgia, serif",
          padding: "2rem",
        }}
      >
        <h1>Algo deu errado</h1>
        <p>Não foi possível abrir esta página.</p>
        <button
          type="button"
          onClick={() => reset()}
          style={{
            marginTop: "1rem",
            minHeight: "44px",
            border: "1px solid #6E2B2B",
            borderRadius: "6px",
            background: "#6E2B2B",
            color: "#FFFFFF",
            padding: "0.5rem 1rem",
          }}
        >
          Tentar de novo
        </button>
      </body>
    </html>
  );
}
