import type { Metadata } from "next";
import { SampleSheets } from "@/components/site/sample-pages";

export const metadata: Metadata = {
  title: "Exemplo de parecer",
  description: "Prévia visual do relatório, a partir de uma obra em domínio público.",
};

export default function ExamplePage() {
  return (
    <article className="mx-auto w-full max-w-[1040px] px-5 py-12 md:py-16">
      <h1 className="measure text-[30px] md:text-[44px]">Exemplo de parecer</h1>
      <p className="measure mt-4 text-[18px] leading-[1.6]">
        Prévia do relatório sobre A Cartomante, de Machado de Assis, obra em domínio público. O PDF
        completo, gerado a partir do texto, entra nesta página numa fase seguinte. O parecer de
        exemplo também é pensado com auxílio de inteligência artificial.
      </p>
      <div className="mt-10">
        <SampleSheets />
      </div>
    </article>
  );
}
