import type { Metadata } from "next";
import { DraftBanner } from "@/components/site/draft-banner";
import { MANUSCRIPT_EXTENSIONS } from "@/lib/uploads/rules";
import { loadSiteContent } from "@/lib/site/content";
import { sellerIdentification } from "@/lib/seller/identification";

export const metadata: Metadata = {
  title: "Termos de uso",
  description: "Rascunho dos termos de uso do Parecer Literário.",
};

export default function TermsPage() {
  const site = loadSiteContent();
  const seller = sellerIdentification(site.seller);
  const formats = MANUSCRIPT_EXTENSIONS.join(", ");

  return (
    <article className="mx-auto w-full max-w-[1040px] px-5 py-12 md:py-16">
      <div className="measure">
        <h1 className="text-[30px] md:text-[44px]">Termos de uso</h1>
        <p className="mt-3 text-[16px] text-muted">Rascunho de setembro de 2026.</p>
        <div className="mt-6">
          <DraftBanner />
        </div>
        <div className="mt-8 space-y-8">
          <section>
            <h2 className="text-[22px]">O serviço</h2>
            <p className="mt-3">
              O Parecer Literário analisa um manuscrito de prosa de ficção e devolve um relatório em
              PDF. {seller[0]}. Contato: {site.seller.contactEmail}.
            </p>
          </section>
          <section id="ia">
            <h2 className="text-[22px]">Natureza automatizada</h2>
            <p className="mt-3">
              O parecer é gerado com auxílio de inteligência artificial. Há medições feitas por
              programas e uma leitura produzida por modelo de linguagem. O resultado é um
              instrumento de revisão. Não é edição humana, preparação de originais nem leitura
              sensível feita por uma pessoa.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Publicação</h2>
            <p className="mt-3">
              O serviço não garante publicação, prêmio, agente ou contrato. A decisão editorial
              continua fora daqui.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Direitos autorais</h2>
            <p className="mt-3">
              Os direitos sobre o manuscrito permanecem com o autor. O envio autoriza apenas o
              processamento necessário para contar palavras, analisar o texto e gerar o relatório.
            </p>
          </section>
          <section id="reembolso">
            <h2 className="text-[22px]">Pagamento e reembolso</h2>
            <p className="mt-3">
              O pagamento é feito por Pix, depois que o orçamento aparece. O orçamento vale por{" "}
              {site.limits.quoteValidityHours} horas. O código Pix de cada cobrança expira em{" "}
              {site.limits.pixExpirationMinutes} minutos. Se o processamento falhar e o parecer não
              for entregue, o reembolso é manual. Este parágrafo ainda precisa de revisão jurídica.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Formatos e limites</h2>
            <p className="mt-3">
              Formatos aceitos: {formats}. Tamanho máximo: {site.maxUploadMb} MB. O serviço é para
              prosa de ficção em português.
            </p>
          </section>
        </div>
      </div>
    </article>
  );
}
