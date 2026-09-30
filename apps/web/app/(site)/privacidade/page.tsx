import type { Metadata } from "next";
import { DraftBanner } from "@/components/site/draft-banner";
import type { SiteContent } from "@/lib/site/content";
import { loadSiteContent } from "@/lib/site/content";
import { sellerIdentification } from "@/lib/seller/identification";

export const metadata: Metadata = {
  title: "Privacidade",
  description: "Rascunho da política de privacidade, em linguagem da LGPD.",
};

export default function PrivacyPage() {
  const site = loadSiteContent();
  const seller = sellerIdentification(site.seller);
  const contact = site.bookxpress.contactEmail.trim() || site.seller.contactEmail;

  return (
    <article className="mx-auto w-full max-w-[1040px] px-5 py-12 md:py-16">
      <div className="measure">
        <h1 className="text-[30px] md:text-[44px]">Privacidade</h1>
        <p className="mt-3 text-[16px] text-muted">Rascunho de setembro de 2026, para a LGPD.</p>
        <div className="mt-6">
          <DraftBanner />
        </div>
        <div className="mt-8 space-y-8">
          <section>
            <h2 className="text-[22px]">Quem trata os dados</h2>
            <p className="mt-3">
              {seller.join(". ")}. O contato do encarregado, neste rascunho, é {contact}.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Dados coletados</h2>
            <p className="mt-3">
              Nome, e-mail, CPF, título da obra, gênero, público-alvo e o arquivo do manuscrito.
              Dados de pagamento são tratados pelo provedor de Pix. O relatório gerado também fica
              guardado pelo prazo abaixo.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Finalidade</h2>
            <p className="mt-3">
              Contar palavras, calcular o preço, cobrar o Pix, analisar o manuscrito, gerar o PDF e
              enviar o resultado por e-mail. O acompanhamento do pedido usa um link com código.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Com quem compartilhamos</h2>
            <p className="mt-3">
              Provedor de pagamento (Pix), provedor de modelo de linguagem (análise do texto),
              provedor de e-mail e armazenamento privado dos arquivos. Não vendemos o manuscrito.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Prazos</h2>
            <p className="mt-3">
              O manuscrito e os arquivos de trabalho são apagados{" "}
              {site.retention.manuscriptDaysAfterDelivery} dias após a entrega. O relatório fica{" "}
              {site.retention.reportDaysAfterDelivery} dias. Esses prazos não apagam o cadastro do
              autor nem o histórico de consentimento.
            </p>
          </section>
          <section>
            <h2 className="text-[22px]">Direitos do titular</h2>
            <p className="mt-3">
              Você pode pedir confirmação, acesso, correção, portabilidade e exclusão, e pode
              revogar consentimentos. O pedido de exclusão apaga ou anonimiza o cadastro e os
              arquivos, e guarda só o mínimo necessário para não reenviar contato. Escreva para{" "}
              {contact}.
            </p>
          </section>
          <BookxpressSection site={site} />
        </div>
      </div>
    </article>
  );
}

function BookxpressSection({ site }: { site: SiteContent }) {
  const bookxpress = site.bookxpress;
  const identity =
    bookxpress.relationship === "parceira"
      ? `A Bookxpress é uma empresa parceira${bookxpress.legalName ? `: ${bookxpress.legalName}` : ""}${bookxpress.cnpj ? `, CNPJ ${bookxpress.cnpj}` : ""}.`
      : bookxpress.legalName
        ? `A Bookxpress é a própria operação deste serviço (${bookxpress.legalName}${bookxpress.cnpj ? `, CNPJ ${bookxpress.cnpj}` : ""}).`
        : "A Bookxpress é a própria operação deste serviço. A razão social e o CNPJ ainda não foram publicados e entram neste texto antes do lançamento.";

  return (
    <section id="bookxpress">
      <h2 className="text-[22px]">Bookxpress</h2>
      <div className="mt-3 space-y-3">
        <p>{identity}</p>
        <p>
          Se você marcar o campo opcional no pedido, tratamos apenas nome e e-mail para enviar
          novidades, dicas para escritores e ofertas. O manuscrito, o título da obra, o CPF e o
          parecer não entram nesse consentimento.
        </p>
        <p>A base legal é o consentimento. O campo nasce desmarcado e não muda o preço.</p>
        <p>
          Dá para cancelar pelo link no rodapé dos e-mails e pela página de preferências, sem login
          e sem formulário obrigatório. Esses caminhos de cancelamento entram com o envio real dos
          e-mails.
        </p>
        <p>
          O histórico do consentimento fica como prova por{" "}
          {site.retention.consentProofYearsAfterRevocation} anos após a revogação.
        </p>
      </div>
    </section>
  );
}
