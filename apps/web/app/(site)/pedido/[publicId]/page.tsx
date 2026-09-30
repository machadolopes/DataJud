import type { Metadata } from "next";
import { DemoNotice } from "@/components/site/demo-notice";
import { loadSiteContent } from "@/lib/site/content";

export const metadata: Metadata = {
  title: "Acompanhar pedido",
  description: "Linha do tempo do pedido, com dados de demonstração.",
};

const stages = [
  "Manuscrito recebido",
  "Orçamento calculado",
  "Pagamento confirmado",
  "Lendo capítulos",
  "Medindo o estilo",
  "Analisando a Jornada do Herói",
  "Escrevendo o parecer",
  "PDF pronto",
];

const currentStage = "Lendo capítulos";

export default async function OrderPage({
  params,
  searchParams,
}: {
  params: Promise<{ publicId: string }>;
  searchParams: Promise<{ t?: string | string[] }>;
}) {
  const { publicId } = await params;
  const query = await searchParams;
  const token = Array.isArray(query.t) ? query.t[0] : query.t;
  const site = loadSiteContent();

  return (
    <article className="mx-auto w-full max-w-[1040px] px-5 py-12 md:py-16">
      <div className="measure">
        <h1 className="text-[30px] md:text-[44px]">Acompanhar pedido</h1>
        <p className="mt-3 text-[16px] text-muted">Pedido {publicId}</p>
        <div className="mt-6">
          <DemoNotice>
            Demonstração. O status real, o código de acesso e o download entram na fase seguinte.
          </DemoNotice>
        </div>
        {token ? (
          <>
            <ol className="mt-8 divide-y divide-line border-y border-line" aria-label="Etapas">
              {stages.map((stage) => {
                const current = stage === currentStage;
                const done = stages.indexOf(stage) < stages.indexOf(currentStage);
                return (
                  <li
                    key={stage}
                    className="flex items-baseline justify-between gap-4 py-3"
                    aria-current={current ? "step" : undefined}
                  >
                    <span className={current ? "font-medium" : "text-ink"}>{stage}</span>
                    <span className="text-[16px] text-muted">
                      {current ? "agora" : done ? "feito" : "depois"}
                    </span>
                  </li>
                );
              })}
            </ol>
            <div className="mt-8">
              <button
                type="button"
                disabled
                aria-describedby="download-hint"
                className="inline-flex min-h-11 items-center rounded-[6px] border border-line px-5 text-[16px] opacity-50"
              >
                Baixar PDF
              </button>
              <p id="download-hint" className="mt-3 text-[16px] leading-[1.6]">
                O download aparece quando o parecer estiver pronto. O link vale{" "}
                {site.limits.downloadUrlMinutes} minutos e é gerado na hora.
              </p>
            </div>
          </>
        ) : (
          <p className="mt-8" role="alert">
            Este link está incompleto. Abra o endereço enviado por e-mail, com o código de acesso.
          </p>
        )}
      </div>
    </article>
  );
}
