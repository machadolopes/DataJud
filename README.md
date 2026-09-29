# Parecer Literário

Produto web que vende pareceres literários automatizados para autores brasileiros de prosa de ficção. O autor envia o manuscrito, recebe um orçamento, paga via Pix e, após a análise, recebe um relatório em PDF por e-mail.

O parecer é gerado com auxílio de inteligência artificial. Idioma da interface, e-mails e relatório: português do Brasil.

Especificação normativa: [`docs/SPEC.md`](docs/SPEC.md). Decisões de engenharia: [`docs/DECISOES.md`](docs/DECISOES.md).

> Fase atual: **F0 — Fundação**. Site, upload, pagamento e pipeline de análise ainda não estão implementados.

## Stack (fixa)

- Monorepo pnpm: `apps/web`, `services/worker`, `packages/shared`
- Next.js 16 (App Router) + TypeScript + Tailwind CSS
- PostgreSQL + Prisma (único dono de migrations)
- Fila na tabela `jobs` (`SELECT … FOR UPDATE SKIP LOCKED`)
- Storage S3-compatível (MinIO no desenvolvimento, Cloudflare R2 em produção)
- Worker Python 3.12 + uv + psycopg 3 + Pydantic v2
- Mocks locais: `PAYMENT_PROVIDER=mock`, `LLM_MODE=mock`, `EMAIL_PROVIDER=mailpit`

## Desenvolvimento local

Pré-requisitos: Node 22, pnpm 10, Docker, [uv](https://docs.astral.sh/uv/).

```bash
cp .env.example .env
docker compose up -d --build
pnpm install
pnpm db:generate
pnpm db:migrate:dev
pnpm dev
```

Serviços locais:

| Serviço       | URL                                             |
| ------------- | ----------------------------------------------- |
| Web           | http://localhost:3000                           |
| MinIO console | http://localhost:9001 (minioadmin / minioadmin) |
| Mailpit       | http://localhost:8025                           |
| Postgres      | localhost:5432 (parecer / parecer)              |

O worker sobe duas instâncias no Compose (`--queue ingest` e `--queue analysis`). Na F0 elas apenas reclamam jobs e os devolvem à fila — o pipeline entra nas fases 2 e 4–6.

```bash
pnpm test
pnpm lint
pnpm seed   # F0: no-op (pedidos de exemplo entram numa fase posterior)
```

## Variáveis de ambiente

Cópia completa, sem valores reais de produção: [`.env.example`](.env.example).

Em produção o app **recusa iniciar** se algum `priceCents` em `config/pricing.json` for `0`, ou se `legalName` / `contactEmail` em `config/consents.json` estiverem vazios.

## E-mail (produção)

Remetente de domínio próprio com SPF, DKIM e DMARC. Documentar os registros no deploy (F7). No desenvolvimento, tudo cai no Mailpit.

## TODO da F0

- [ ] Preencher `config/pricing.json` com preços reais antes de qualquer deploy.
- [ ] Preencher `legalName`, `cnpj` e `contactEmail` em `config/consents.json` e `config/seller.json`.
- [ ] Confirmar identificadores dos modelos Anthropic na documentação oficial (F5).
- [ ] Confirmar preços em `config/llm_prices.json` (valores de exemplo).
- [ ] Dependências de PLN, extração, LLM e PDF no worker (fases 4–6).
- [ ] `pnpm seed` com pedidos em vários status (F2+).
- [ ] Adapters de pagamento, e-mail, storage e admin (fases 2–7).
- [ ] Textos de termos e privacidade para revisão jurídica (F1).
- [ ] Notebook `DATAJUD_API_v_final.ipynb` nesta raiz é legado do repositório; fora do produto.

## Fora de escopo (v1)

Contas de usuário, carrinho, cartão de crédito, poesia, outros idiomas, tema escuro, edição do texto, chat, NF-e automática, aplicativo móvel. Ver seção 22 da spec.
