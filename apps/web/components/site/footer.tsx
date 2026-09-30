import Link from "next/link";
import type { SellerConfig } from "@/lib/config";
import { sellerIdentification } from "@/lib/seller/identification";

export function Footer({ seller }: { seller: SellerConfig }) {
  const lines = sellerIdentification(seller);
  return (
    <footer className="border-t border-line">
      <div className="mx-auto grid w-full max-w-[1040px] gap-8 px-5 py-12 md:grid-cols-[minmax(0,680px)_1fr]">
        <div>
          <p className="font-serif text-[22px]">Parecer Literário</p>
          <p className="measure mt-3 text-[16px] leading-[1.6]">
            O parecer é gerado com auxílio de inteligência artificial.
          </p>
          <ul className="mt-6 flex flex-col gap-2 text-[16px] sm:flex-row sm:gap-6">
            <li>
              <Link href="/termos" className="underline decoration-line underline-offset-4">
                Termos
              </Link>
            </li>
            <li>
              <Link href="/privacidade" className="underline decoration-line underline-offset-4">
                Privacidade
              </Link>
            </li>
            <li>
              <a
                href={`mailto:${seller.contactEmail}`}
                className="underline decoration-line underline-offset-4"
              >
                Contato
              </a>
            </li>
          </ul>
        </div>
        <div className="text-[16px] leading-[1.6]">
          <p className="text-muted">Identificação do vendedor</p>
          {lines.map((line) => (
            <p key={line}>{line}</p>
          ))}
          <p>
            <a
              href={`mailto:${seller.contactEmail}`}
              className="underline decoration-line underline-offset-4"
            >
              {seller.contactEmail}
            </a>
          </p>
        </div>
      </div>
    </footer>
  );
}
