import Link from "next/link";

const links = [
  { href: "/#como-funciona", label: "Como funciona" },
  { href: "/#precos", label: "Preços" },
  { href: "/exemplo", label: "Exemplo" },
  { href: "/analisar", label: "Analisar meu manuscrito" },
];

export function Header() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-paper">
      <div className="mx-auto flex w-full max-w-[1040px] items-center justify-between gap-4 px-5 py-3">
        <Link href="/" className="font-serif text-[22px] leading-none text-ink">
          Parecer Literário
        </Link>
        <nav aria-label="Principal" className="hidden items-center gap-6 md:flex">
          {links.slice(0, 3).map((link) => (
            <Link key={link.href} href={link.href} className="text-[16px] text-ink">
              {link.label}
            </Link>
          ))}
          <Link
            href="/analisar"
            className="inline-flex min-h-11 items-center rounded-[6px] border border-accent bg-accent px-4 text-[16px] text-accent-ink"
          >
            Analisar meu manuscrito
          </Link>
        </nav>
        <details className="relative md:hidden">
          <summary className="flex min-h-11 cursor-pointer items-center rounded-[6px] border border-line px-3 text-[16px]">
            Menu
          </summary>
          <nav
            aria-label="Principal no celular"
            className="absolute right-0 mt-2 w-64 border border-line bg-paper p-2"
          >
            <ul>
              {links.map((link) => (
                <li key={link.href}>
                  <Link href={link.href} className="block px-3 py-3 text-[16px] text-ink">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </details>
      </div>
    </header>
  );
}
