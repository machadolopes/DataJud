import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { BookxpressOptIn } from "@/components/wizard/bookxpress-opt-in";

describe("BookxpressOptIn", () => {
  it("renders unchecked, with the configured label and the privacy link", () => {
    const html = renderToStaticMarkup(
      <BookxpressOptIn
        label="Quero receber por e-mail novidades, dicas para escritores e ofertas da Bookxpress. Posso cancelar a qualquer momento."
        details="Usaremos apenas seu nome e e-mail."
        checked={false}
        onCheckedChange={() => undefined}
      />,
    );
    expect(html).toContain('aria-checked="false"');
    expect(html).not.toContain('aria-checked="true"');
    expect(html).toContain("Quero receber por e-mail novidades");
    expect(html).toContain('href="/privacidade#bookxpress"');
    expect(html).toContain("Saiba mais");
  });
});
