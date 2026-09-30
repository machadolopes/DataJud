import Link from "next/link";
import { PricingTable } from "@/components/site/pricing-table";
import { SampleThumbnails } from "@/components/site/sample-pages";
import { Button } from "@/components/ui/button";
import { MANUSCRIPT_EXTENSIONS } from "@/lib/uploads/rules";
import { loadSiteContent } from "@/lib/site/content";

export default function HomePage() {
  const site = loadSiteContent();
  const formats = MANUSCRIPT_EXTENSIONS.join(", ");
  const faqs = [
    {
      question: "Em quanto tempo o parecer fica pronto?",
      answer:
        "Normalmente em até 1 hora depois da confirmação do Pix. O prazo máximo é de 24 horas.",
    },
    {
      question: "Meu manuscrito fica confidencial?",
      answer: `Sim. O arquivo fica em armazenamento privado, e o acompanhamento do pedido usa um link com código enviado ao seu e-mail. O manuscrito é apagado ${site.retention.manuscriptDaysAfterDelivery} dias após a entrega. O relatório fica disponível por ${site.retention.reportDaysAfterDelivery} dias.`,
    },
    {
      question: "Vocês usam inteligência artificial?",
      answer:
        "Sim. Parte da leitura é feita por programas no nosso servidor e parte por um modelo de linguagem. O parecer é gerado com auxílio de inteligência artificial.",
    },
    {
      question: "Quais formatos são aceitos?",
      answer: `${formats.toUpperCase().replaceAll(".", "")}. O arquivo pode ter até ${site.maxUploadMb} MB.`,
    },
    {
      question: "E se eu pedir reembolso?",
      answer: `Se o processamento falhar e o parecer não for entregue, o reembolso é feito manualmente. O orçamento vale por ${site.limits.quoteValidityHours} horas. A política completa está em rascunho nos termos e ainda passa por revisão jurídica.`,
    },
    {
      question: "A IA substitui um editor humano?",
      answer:
        "Não. O parecer aponta padrões, hipóteses e caminhos de revisão. Ele não reescreve o livro, não garante publicação e não ocupa o lugar de um editor, de um preparador ou de uma leitura feita por uma pessoa.",
    },
  ];

  return (
    <>
      <section className="border-b border-line">
        <div className="mx-auto w-full max-w-[1040px] px-5 py-16 md:py-24">
          <p className="font-serif text-[18px] italic text-muted">
            Para autores de prosa de ficção
          </p>
          <h1 className="measure mt-4 text-[30px] md:text-[44px]">
            Um parecer profundo sobre o seu livro, em poucas horas.
          </h1>
          <p className="measure mt-6 text-[18px] leading-[1.6]">
            Medimos o texto — vocabulário, ritmo e estrutura — e entregamos uma leitura crítica
            escrita com auxílio de inteligência artificial.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild>
              <Link href="/analisar">Analisar meu manuscrito</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/exemplo">Ver um exemplo</Link>
            </Button>
          </div>
        </div>
      </section>

      <section id="como-funciona" className="border-b border-line">
        <div className="mx-auto w-full max-w-[1040px] px-5 py-14 md:py-20">
          <h2 className="text-[30px]">Como funciona</h2>
          <ol className="mt-8 grid gap-4 md:grid-cols-3">
            <li className="border border-line p-5">
              <p className="font-serif text-[22px]">1</p>
              <h3 className="mt-3 text-[22px]">Envie o arquivo</h3>
              <p className="mt-2 text-[16px] leading-[1.6] text-muted">
                {formats.toUpperCase().replaceAll(".", "")}. Você vê o preço antes de pagar.
              </p>
            </li>
            <li className="border border-line p-5">
              <p className="font-serif text-[22px]">2</p>
              <h3 className="mt-3 text-[22px]">Pague com Pix</h3>
              <p className="mt-2 text-[16px] leading-[1.6] text-muted">
                O valor segue a faixa de palavras do manuscrito.
              </p>
            </li>
            <li className="border border-line p-5">
              <p className="font-serif text-[22px]">3</p>
              <h3 className="mt-3 text-[22px]">Receba o parecer</h3>
              <p className="mt-2 text-[16px] leading-[1.6] text-muted">
                O PDF chega no seu e-mail, com um link para baixar de novo.
              </p>
            </li>
          </ol>
        </div>
      </section>

      <section id="parecer" className="border-b border-line">
        <div className="mx-auto w-full max-w-[1040px] px-5 py-14 md:py-20">
          <h2 className="measure text-[30px]">O que o parecer inclui</h2>
          <p className="measure mt-4 border-l border-accent pl-4 text-[18px] leading-[1.6]">
            O parecer é gerado com auxílio de inteligência artificial.
          </p>
          <ul className="mt-8 grid gap-4 sm:grid-cols-2">
            {[
              ["Estilo e linguagem", "Vocabulário, variação de frase e marcas da prosa."],
              ["Ritmo e estrutura", "Como os capítulos se sucedem e onde a trama respira."],
              ["Sentimento por capítulo", "A curva emocional ao longo do livro."],
              ["Jornada do Herói", "Onde o arco aparece e onde ele falha."],
              ["Leitura de sensibilidade", "Trechos com conteúdo potencialmente ofensivo."],
              ["Parecer do crítico", "Uma leitura motivacional, honesta e fraterna."],
            ].map(([title, body]) => (
              <li key={title} className="border border-line p-5">
                <h3 className="text-[22px]">{title}</h3>
                <p className="mt-2 text-[16px] leading-[1.6] text-muted">{body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section id="amostra" className="border-b border-line">
        <div className="mx-auto w-full max-w-[1040px] px-5 py-14 md:py-20">
          <h2 className="text-[30px]">Amostra</h2>
          <p className="measure mt-4 text-[18px] leading-[1.6]">
            Três páginas de um relatório de exemplo, no mesmo desenho do PDF. A obra da amostra é de
            domínio público.
          </p>
          <div className="mt-8">
            <SampleThumbnails />
          </div>
          <p className="mt-6">
            <Link href="/exemplo" className="underline decoration-line underline-offset-4">
              Ver o exemplo
            </Link>
          </p>
        </div>
      </section>

      <section id="precos" className="border-b border-line">
        <div className="mx-auto w-full max-w-[1040px] px-5 py-14 md:py-20">
          <h2 className="text-[30px]">Preços</h2>
          <p className="measure mt-4 text-[18px] leading-[1.6]">
            O preço depende do número de palavras. Você vê o valor exato antes de pagar.
          </p>
          <div className="mt-8">
            <PricingTable pricing={site.pricing} pricesUnpublished={site.pricesUnpublished} />
          </div>
        </div>
      </section>

      <section id="faq" className="border-b border-line">
        <div className="mx-auto w-full max-w-[1040px] px-5 py-14 md:py-20">
          <h2 className="text-[30px]">Perguntas frequentes</h2>
          <div className="mt-8 divide-y divide-line border-y border-line">
            {faqs.map((item) => (
              <details key={item.question} className="py-4">
                <summary className="cursor-pointer text-[18px]">{item.question}</summary>
                <p className="measure mt-3 text-[16px] leading-[1.6] text-muted">{item.answer}</p>
              </details>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}
