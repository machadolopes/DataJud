import type { Metadata } from "next";
import "./globals.css";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Parecer Literário",
  description:
    "Um parecer profundo sobre o seu livro, em poucas horas. Análise quantitativa e leitura crítica com auxílio de inteligência artificial.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
