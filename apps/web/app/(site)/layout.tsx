import type { ReactNode } from "react";
import { Footer } from "@/components/site/footer";
import { Header } from "@/components/site/header";
import { loadSiteContent } from "@/lib/site/content";

export default function SiteLayout({ children }: { children: ReactNode }) {
  const site = loadSiteContent();
  return (
    <div className="flex flex-1 flex-col">
      <a className="skip-link" href="#conteudo">
        Ir para o conteúdo
      </a>
      <Header />
      <main id="conteudo" tabIndex={-1} className="flex-1 outline-none">
        {children}
      </main>
      <Footer seller={site.seller} />
    </div>
  );
}
