import Link from "next/link";
import { Footer } from "@/components/site/footer";
import { Header } from "@/components/site/header";
import { loadSiteContent } from "@/lib/site/content";

export default function NotFound() {
  const site = loadSiteContent();
  return (
    <div className="flex flex-1 flex-col">
      <Header />
      <main id="conteudo" className="mx-auto w-full max-w-[1040px] flex-1 px-5 py-16">
        <h1 className="text-[30px] md:text-[44px]">Página não encontrada</h1>
        <p className="measure mt-4">O endereço não corresponde a uma página deste site.</p>
        <p className="mt-6">
          <Link href="/" className="underline decoration-line underline-offset-4">
            Voltar ao início
          </Link>
        </p>
      </main>
      <Footer seller={site.seller} />
    </div>
  );
}
