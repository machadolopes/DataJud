import type { Metadata } from "next";
import { Wizard } from "@/components/wizard/wizard";
import { DEMO_ANALYSIS } from "@/lib/demo/fixture";
import { equivalentPages } from "@/lib/format";
import { priceForWordCount } from "@/lib/pricing";
import { loadSiteContent } from "@/lib/site/content";

export const metadata: Metadata = {
  title: "Analisar manuscrito",
  description: "Envie o manuscrito, veja o orçamento e siga para o Pix.",
};

export default function AnalyzePage() {
  const site = loadSiteContent();
  const price = priceForWordCount(DEMO_ANALYSIS.wordCount, site.pricing);
  return (
    <Wizard
      maxUploadMb={site.maxUploadMb}
      wordsPerPage={site.limits.wordsPerPage}
      pixExpirationMinutes={site.limits.pixExpirationMinutes}
      bookxpressLabel={site.bookxpress.label}
      bookxpressDetails={site.bookxpress.details}
      quote={{
        wordCount: DEMO_ANALYSIS.wordCount,
        chapterCount: DEMO_ANALYSIS.chapterCount,
        pages: equivalentPages(DEMO_ANALYSIS.wordCount, site.limits.wordsPerPage),
        tierLabel: price.label,
        priceCents: price.priceCents,
        currency: price.currency,
      }}
    />
  );
}
