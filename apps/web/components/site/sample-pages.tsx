import Link from "next/link";

const pages = [
  {
    id: "capa",
    kicker: "Capa",
    title: "A Cartomante",
    lines: [
      "Obra de domínio público de Machado de Assis.",
      "Parecer de exemplo, no desenho do relatório final.",
      "Gerado com auxílio de inteligência artificial.",
    ],
  },
  {
    id: "sentimento",
    kicker: "Sentimento por capítulo",
    title: "A curva da cena",
    lines: [
      "O trecho da consulta oscila entre curiosidade e temor.",
      "A queda de tom depois da revelação pede mais ar.",
      "Indicador, não sentença.",
    ],
  },
  {
    id: "critico",
    kicker: "Parecer do crítico",
    title: "Correção fraterna",
    lines: [
      "O diálogo carrega a trama com economia.",
      "O final entrega o fato e esconde a consequência.",
      "Um caminho: reescrever só a última troca de falas.",
    ],
  },
] as const;

export function SampleThumbnails() {
  return (
    <ul className="grid gap-4 sm:grid-cols-3">
      {pages.map((page) => (
        <li key={page.id}>
          <Link
            href={`/exemplo#${page.id}`}
            className="flex aspect-[3/4] flex-col border border-line p-4"
          >
            <span className="text-[14px] text-muted">{page.kicker}</span>
            <span className="mt-3 font-serif text-[22px] leading-tight">{page.title}</span>
            <span className="mt-4 line-clamp-4 text-[14px] leading-[1.6] text-ink">
              {page.lines[0]}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function SampleSheets() {
  return (
    <div className="flex flex-col gap-8">
      {pages.map((page) => (
        <article key={page.id} id={page.id} className="border border-line p-6 md:p-10">
          <p className="text-[14px] text-muted">{page.kicker}</p>
          <h2 className="mt-3 text-[30px]">{page.title}</h2>
          <div className="measure mt-6 space-y-4">
            {page.lines.map((line) => (
              <p key={line}>{line}</p>
            ))}
          </div>
        </article>
      ))}
    </div>
  );
}
