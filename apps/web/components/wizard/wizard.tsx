"use client";

import Link from "next/link";
import {
  useEffect,
  useId,
  useRef,
  useState,
  type ComponentProps,
  type FormEvent,
  type ReactNode,
  type RefObject,
} from "react";
import { DemoNotice } from "@/components/site/demo-notice";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BookxpressOptIn } from "@/components/wizard/bookxpress-opt-in";
import { DEMO_MANUSCRIPT_NAME, DEMO_ORDER, DEMO_PIX_CODE } from "@/lib/demo/fixture";
import { formatBytes, formatCents, formatCountdown, formatInteger, maskCpf } from "@/lib/format";
import {
  demoChaptersDetected,
  isAcceptedManuscript,
  MANUSCRIPT_EXTENSIONS,
  maxUploadBytes,
} from "@/lib/uploads/rules";
import {
  audienceOptions,
  emptyWorkForm,
  fieldErrors,
  genreOptions,
  workSchema,
} from "@/lib/wizard/schema";

const steps = ["Manuscrito", "Obra e você", "Orçamento", "Pagamento"] as const;

type ManuscriptSelection = {
  name: string;
  sizeLabel: string;
  chaptersDetected: boolean;
};

type Quote = {
  wordCount: number;
  chapterCount: number;
  pages: number;
  tierLabel: string;
  priceCents: number;
  currency: string;
};

type WizardProps = {
  quote: Quote;
  wordsPerPage: number;
  pixExpirationMinutes: number;
  maxUploadMb: number;
  bookxpressLabel: string;
  bookxpressDetails: string;
};

type Phase = 1 | 2 | 3 | 4 | "calculating" | "success";

export function Wizard({
  quote,
  wordsPerPage,
  pixExpirationMinutes,
  maxUploadMb,
  bookxpressLabel,
  bookxpressDetails,
}: WizardProps) {
  const [phase, setPhase] = useState<Phase>(1);
  const [manuscript, setManuscript] = useState<ManuscriptSelection | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [work, setWork] = useState(emptyWorkForm);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const headingRef = useRef<HTMLHeadingElement>(null);
  const errorSummaryRef = useRef<HTMLDivElement>(null);

  const progressIndex = phase === "calculating" ? 2 : phase === "success" ? 4 : phase;

  useEffect(() => {
    headingRef.current?.focus();
  }, [phase]);

  function selectFile(file: File | null) {
    if (!file) return;
    if (!isAcceptedManuscript(file.name)) {
      setManuscript(null);
      setFileError(
        `Formato não aceito. Use ${MANUSCRIPT_EXTENSIONS.join(", ").replaceAll(".", "").toUpperCase()}.`,
      );
      return;
    }
    if (file.size <= 0) {
      setManuscript(null);
      setFileError("O arquivo está vazio.");
      return;
    }
    if (file.size > maxUploadBytes(maxUploadMb)) {
      setManuscript(null);
      setFileError(`O arquivo passa de ${maxUploadMb} MB.`);
      return;
    }
    setFileError(null);
    setManuscript({
      name: file.name,
      sizeLabel: formatBytes(file.size),
      chaptersDetected: demoChaptersDetected(file.name),
    });
  }

  function useDemoManuscript() {
    setFileError(null);
    setManuscript({
      name: DEMO_MANUSCRIPT_NAME,
      sizeLabel: "demonstração",
      chaptersDetected: true,
    });
  }

  function continueFromFile() {
    if (!manuscript) {
      setFileError("Escolha um arquivo para continuar.");
      return;
    }
    setPhase(2);
  }

  function submitWork(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsed = workSchema.safeParse(work);
    if (!parsed.success) {
      setErrors(fieldErrors(parsed.error));
      queueMicrotask(() => errorSummaryRef.current?.focus());
      return;
    }
    setErrors({});
    setPhase("calculating");
    window.setTimeout(() => setPhase(3), 1600);
  }

  return (
    <div className="mx-auto w-full max-w-[1040px] px-5 py-12 md:py-16">
      <p className="text-[16px] text-muted">Passo {progressIndex} de 4</p>
      <ol aria-label="Progresso do pedido" className="mt-3 flex flex-wrap gap-x-4 gap-y-2">
        {steps.map((label, index) => {
          const number = index + 1;
          const current = progressIndex === number && phase !== "success";
          const done = progressIndex > number || phase === "success";
          return (
            <li key={label} className="text-[16px]">
              {done && phase !== "success" ? (
                <button
                  type="button"
                  className="underline decoration-line underline-offset-4"
                  onClick={() => setPhase(number as Phase)}
                >
                  {number}. {label}
                </button>
              ) : (
                <span
                  aria-current={current ? "step" : undefined}
                  className={current ? "text-ink" : "text-muted"}
                >
                  {number}. {label}
                </span>
              )}
            </li>
          );
        })}
      </ol>

      <div className="mt-8 max-w-[680px]">
        <DemoNotice>
          Demonstração. O arquivo não sai deste navegador e nenhum Pix é cobrado.
        </DemoNotice>
      </div>

      <div className="mt-8 max-w-[680px]">
        {phase === 1 ? (
          <ManuscriptStep
            headingRef={headingRef}
            maxUploadMb={maxUploadMb}
            manuscript={manuscript}
            fileError={fileError}
            onFile={selectFile}
            onDemo={useDemoManuscript}
            onContinue={continueFromFile}
          />
        ) : null}
        {phase === 2 ? (
          <WorkStep
            headingRef={headingRef}
            errorSummaryRef={errorSummaryRef}
            work={work}
            errors={errors}
            bookxpressLabel={bookxpressLabel}
            bookxpressDetails={bookxpressDetails}
            onChange={setWork}
            onSubmit={submitWork}
            onBack={() => setPhase(1)}
          />
        ) : null}
        {phase === "calculating" ? (
          <section aria-live="polite" aria-busy="true">
            <h1 ref={headingRef} tabIndex={-1} className="text-[30px] outline-none">
              Calculando orçamento...
            </h1>
            <p className="mt-4">Estamos lendo o tamanho do manuscrito.</p>
          </section>
        ) : null}
        {phase === 3 && manuscript ? (
          <QuoteStep
            headingRef={headingRef}
            manuscript={manuscript}
            quote={quote}
            wordsPerPage={wordsPerPage}
            onBack={() => setPhase(2)}
            onPay={() => setPhase(4)}
          />
        ) : null}
        {phase === 4 ? (
          <PaymentStep
            headingRef={headingRef}
            quote={quote}
            pixExpirationMinutes={pixExpirationMinutes}
            onBack={() => setPhase(3)}
            onConfirmed={() => setPhase("success")}
          />
        ) : null}
        {phase === "success" ? <SuccessStep headingRef={headingRef} title={work.title} /> : null}
      </div>
    </div>
  );
}

function ManuscriptStep({
  headingRef,
  maxUploadMb,
  manuscript,
  fileError,
  onFile,
  onDemo,
  onContinue,
}: {
  headingRef: RefObject<HTMLHeadingElement | null>;
  maxUploadMb: number;
  manuscript: ManuscriptSelection | null;
  fileError: string | null;
  onFile: (file: File | null) => void;
  onDemo: () => void;
  onContinue: () => void;
}) {
  const errorId = useId();
  const [dragging, setDragging] = useState(false);

  return (
    <section>
      <h1 ref={headingRef} tabIndex={-1} className="text-[30px] outline-none">
        Manuscrito
      </h1>
      <p className="mt-4">
        Aceitamos {MANUSCRIPT_EXTENSIONS.join(", ")} até {maxUploadMb} MB.
      </p>
      <label
        htmlFor="manuscript"
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          onFile(event.dataTransfer.files.item(0));
        }}
        className={`mt-6 flex cursor-pointer flex-col gap-3 border p-6 ${dragging ? "border-accent" : "border-line"}`}
      >
        <span className="font-serif text-[22px]">Solte o arquivo aqui</span>
        <span className="text-[16px] leading-snug text-muted">ou escolha no seu computador.</span>
        <input
          id="manuscript"
          name="manuscript"
          type="file"
          accept={MANUSCRIPT_EXTENSIONS.join(",")}
          aria-invalid={fileError ? true : undefined}
          aria-describedby={fileError ? errorId : undefined}
          className="block w-full text-[16px] file:mr-3 file:min-h-11 file:rounded-[6px] file:border file:border-ink file:bg-paper file:px-4 file:text-[16px] file:text-ink"
          onChange={(event) => onFile(event.target.files?.item(0) ?? null)}
        />
      </label>
      {fileError ? (
        <p id={errorId} role="alert" className="mt-3 text-[16px] text-danger">
          {fileError}
        </p>
      ) : null}
      {manuscript ? (
        <p className="mt-4 text-[16px]" aria-live="polite">
          Arquivo: {manuscript.name} ({manuscript.sizeLabel})
        </p>
      ) : null}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <Button type="button" onClick={onContinue}>
          Continuar
        </Button>
        <Button type="button" variant="outline" onClick={onDemo}>
          Usar manuscrito de demonstração
        </Button>
      </div>
    </section>
  );
}

function WorkStep({
  headingRef,
  errorSummaryRef,
  work,
  errors,
  bookxpressLabel,
  bookxpressDetails,
  onChange,
  onSubmit,
  onBack,
}: {
  headingRef: RefObject<HTMLHeadingElement | null>;
  errorSummaryRef: RefObject<HTMLDivElement | null>;
  work: ReturnType<typeof emptyWorkForm>;
  errors: Record<string, string>;
  bookxpressLabel: string;
  bookxpressDetails: string;
  onChange: (value: ReturnType<typeof emptyWorkForm>) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onBack: () => void;
}) {
  const errorList = Object.values(errors);
  function set<K extends keyof typeof work>(key: K, value: (typeof work)[K]) {
    onChange({ ...work, [key]: value });
  }

  return (
    <section>
      <h1 ref={headingRef} tabIndex={-1} className="text-[30px] outline-none">
        Sobre a obra e você
      </h1>
      <form className="mt-6 flex flex-col gap-5" noValidate onSubmit={onSubmit}>
        {errorList.length > 0 ? (
          <div
            ref={errorSummaryRef}
            tabIndex={-1}
            role="alert"
            className="border border-danger px-4 py-3 text-[16px] outline-none"
          >
            <p>Revise os campos abaixo.</p>
            <ul className="mt-2 list-disc pl-5">
              {errorList.map((message) => (
                <li key={message}>{message}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <TextField
          id="author-name"
          label="Nome"
          autoComplete="name"
          value={work.name}
          error={errors.name}
          onChange={(value) => set("name", value)}
        />
        <TextField
          id="author-email"
          label="E-mail"
          type="email"
          autoComplete="email"
          value={work.email}
          error={errors.email}
          onChange={(value) => set("email", value)}
        />
        <TextField
          id="author-email-confirm"
          label="Confirme o e-mail"
          type="email"
          autoComplete="off"
          value={work.emailConfirm}
          error={errors.emailConfirm}
          onChange={(value) => set("emailConfirm", value)}
        />
        <TextField
          id="author-cpf"
          label="CPF"
          inputMode="numeric"
          autoComplete="off"
          value={work.cpf}
          error={errors.cpf}
          onChange={(value) => set("cpf", maskCpf(value))}
        />
        <TextField
          id="work-title"
          label="Título da obra"
          value={work.title}
          error={errors.title}
          onChange={(value) => set("title", value)}
        />
        <SelectField
          id="work-genre"
          label="Gênero"
          value={work.genre}
          error={errors.genre}
          placeholder="Selecione"
          options={genreOptions}
          onChange={(value) => set("genre", value)}
        />
        <SelectField
          id="work-audience"
          label="Público-alvo"
          value={work.audience}
          error={errors.audience}
          placeholder="Selecione"
          options={audienceOptions}
          onChange={(value) => set("audience", value)}
        />
        <fieldset className="flex flex-col gap-4 border-0 p-0">
          <legend className="text-[16px]">Aceites obrigatórios</legend>
          <ConsentCheck
            id="accept-terms"
            checked={work.acceptTerms}
            error={errors.acceptTerms}
            onCheckedChange={(checked) => set("acceptTerms", checked)}
          >
            Li e aceito os{" "}
            <Link href="/termos" className="underline underline-offset-4">
              termos de uso
            </Link>
            .
          </ConsentCheck>
          <ConsentCheck
            id="accept-ai"
            checked={work.acceptAi}
            error={errors.acceptAi}
            onCheckedChange={(checked) => set("acceptAi", checked)}
          >
            Estou ciente de que o parecer é gerado com auxílio de inteligência artificial e de que o
            texto pode ser processado por provedores externos.
          </ConsentCheck>
        </fieldset>
        <BookxpressOptIn
          label={bookxpressLabel}
          details={bookxpressDetails}
          checked={work.bookxpressOptIn}
          onCheckedChange={(checked) => set("bookxpressOptIn", checked)}
        />
        <div className="mt-2 flex flex-col gap-3 sm:flex-row">
          <Button type="submit">Ver orçamento</Button>
          <Button type="button" variant="outline" onClick={onBack}>
            Voltar
          </Button>
        </div>
      </form>
    </section>
  );
}

function QuoteStep({
  headingRef,
  manuscript,
  quote,
  wordsPerPage,
  onBack,
  onPay,
}: {
  headingRef: RefObject<HTMLHeadingElement | null>;
  manuscript: ManuscriptSelection;
  quote: Quote;
  wordsPerPage: number;
  onBack: () => void;
  onPay: () => void;
}) {
  return (
    <section>
      <h1 ref={headingRef} tabIndex={-1} className="text-[30px] outline-none">
        Orçamento
      </h1>
      <p className="mt-4 text-[16px] leading-[1.6]">
        Estes números são de demonstração. A contagem real do arquivo entra na fase seguinte.
        Arquivo: {manuscript.name}.
      </p>
      <dl className="mt-6 divide-y divide-line border-y border-line">
        <QuoteRow term="Palavras" value={formatInteger(quote.wordCount)} />
        <QuoteRow
          term="Capítulos"
          value={manuscript.chaptersDetected ? formatInteger(quote.chapterCount) : "não detectados"}
        />
        <QuoteRow
          term="Páginas equivalentes"
          value={`${formatInteger(quote.pages)} (palavras ÷ ${wordsPerPage})`}
        />
        <QuoteRow term="Faixa" value={quote.tierLabel} />
        <QuoteRow term="Preço" value={formatCents(quote.priceCents, quote.currency)} />
      </dl>
      {manuscript.chaptersDetected ? null : (
        <p className="mt-4 border border-warning px-4 py-3 text-[16px]" role="status">
          Não foi possível identificar capítulos. O texto será dividido em blocos.
        </p>
      )}
      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <Button type="button" onClick={onPay}>
          Pagar com Pix
        </Button>
        <Button type="button" variant="outline" onClick={onBack}>
          Voltar
        </Button>
      </div>
    </section>
  );
}

function PaymentStep({
  headingRef,
  quote,
  pixExpirationMinutes,
  onBack,
  onConfirmed,
}: {
  headingRef: RefObject<HTMLHeadingElement | null>;
  quote: Quote;
  pixExpirationMinutes: number;
  onBack: () => void;
  onConfirmed: () => void;
}) {
  const [remaining, setRemaining] = useState(pixExpirationMinutes * 60);
  const [polls, setPolls] = useState(0);
  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  const codeRef = useRef<HTMLInputElement>(null);
  const expired = remaining <= 0;

  useEffect(() => {
    if (expired) return;
    const id = window.setInterval(() => {
      setRemaining((value) => (value > 0 ? value - 1 : 0));
    }, 1000);
    return () => window.clearInterval(id);
  }, [expired]);

  useEffect(() => {
    if (expired) return;
    const id = window.setInterval(() => {
      setPolls((value) => value + 1);
    }, 3000);
    return () => window.clearInterval(id);
  }, [expired]);

  async function copyCode() {
    setCopied(false);
    setCopyFailed(false);
    try {
      await navigator.clipboard.writeText(DEMO_PIX_CODE);
      setCopied(true);
    } catch {
      codeRef.current?.focus();
      codeRef.current?.select();
      setCopyFailed(true);
    }
  }

  return (
    <section>
      <h1 ref={headingRef} tabIndex={-1} className="text-[30px] outline-none">
        Pagamento
      </h1>
      <p className="mt-4">
        Valor: {formatCents(quote.priceCents, quote.currency)}. Código de demonstração: nenhum
        pagamento é processado.
      </p>
      <div className="mt-6 flex flex-col gap-6 sm:flex-row sm:items-start">
        <QrMark />
        <div className="min-w-0 flex-1">
          <Label htmlFor="pix-code">Código Pix</Label>
          <Input
            ref={codeRef}
            id="pix-code"
            className="mt-2"
            readOnly
            value={DEMO_PIX_CODE}
            aria-describedby="pix-status"
          />
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <Button
              type="button"
              variant="outline"
              onClick={() => void copyCode()}
              disabled={expired}
            >
              Copiar código Pix
            </Button>
            <Button type="button" onClick={onConfirmed} disabled={expired}>
              Simular confirmação do Pix
            </Button>
          </div>
          <p id="pix-status" className="mt-4 text-[16px]" aria-live="polite">
            {expired
              ? "O código expirou."
              : polls === 0
                ? "Aguardando a confirmação do Pix."
                : `Verificando o pagamento… (consulta ${polls})`}
          </p>
          <p className="mt-2 font-serif text-[30px]" aria-live="off">
            <span className="sr-only">Tempo restante </span>
            {formatCountdown(remaining)}
          </p>
          {copied ? <p className="mt-2 text-[16px] text-success">Código copiado.</p> : null}
          {copyFailed ? (
            <p className="mt-2 text-[16px]">Selecione o código e copie manualmente.</p>
          ) : null}
          {expired ? (
            <Button
              type="button"
              className="mt-4"
              variant="outline"
              onClick={() => {
                setRemaining(pixExpirationMinutes * 60);
                setPolls(0);
                setCopied(false);
                setCopyFailed(false);
              }}
            >
              Gerar novo código
            </Button>
          ) : null}
        </div>
      </div>
      <div className="mt-6">
        <Button type="button" variant="outline" onClick={onBack}>
          Voltar
        </Button>
      </div>
    </section>
  );
}

function SuccessStep({
  headingRef,
  title,
}: {
  headingRef: RefObject<HTMLHeadingElement | null>;
  title: string;
}) {
  const href = `/pedido/${DEMO_ORDER.publicId}?t=${DEMO_ORDER.accessToken}`;
  return (
    <section>
      <h1 ref={headingRef} tabIndex={-1} className="text-[30px] outline-none">
        Pagamento confirmado
      </h1>
      <p className="mt-4">
        Recebemos a demonstração{title ? ` de “${title}”` : ""}. O parecer fica pronto normalmente
        em até 1 hora; no máximo 24 horas.
      </p>
      <p className="mt-4 text-[16px] leading-[1.6]">
        Quando o pedido for real, este mesmo link também chega por e-mail.
      </p>
      <div className="mt-6">
        <Button asChild>
          <Link href={href}>Acompanhar o pedido</Link>
        </Button>
      </div>
    </section>
  );
}

function QuoteRow({ term, value }: { term: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-3">
      <dt className="text-[16px] text-muted">{term}</dt>
      <dd className="text-right text-[18px]">{value}</dd>
    </div>
  );
}

function QrMark() {
  const cells = [
    "111111100001111111",
    "100000101010100001",
    "101110101110101101",
    "101110100000101101",
    "101110101011101101",
    "100000101010100001",
    "111111101010111111",
    "000000001110000000",
    "110010111000101110",
    "001101000111010001",
    "111000101000111010",
    "000110111101000111",
    "011010000111101100",
    "000000001011010101",
    "111111101000101011",
    "100000101110111000",
    "101110100010001011",
    "111111100101110101",
  ];
  return (
    <div className="shrink-0">
      <div className="border border-line p-3" aria-hidden="true">
        <svg viewBox="0 0 18 18" className="size-40">
          {cells.map((row, y) =>
            row
              .split("")
              .map((cell, x) =>
                cell === "1" ? (
                  <rect key={`${x}-${y}`} x={x} y={y} width="1" height="1" fill="#1C1B19" />
                ) : null,
              ),
          )}
        </svg>
      </div>
      <p className="sr-only">QR Code Pix de demonstração</p>
    </div>
  );
}

function TextField({
  id,
  label,
  error,
  onChange,
  ...props
}: {
  id: string;
  label: string;
  error?: string;
  onChange: (value: string) => void;
} & Omit<ComponentProps<"input">, "onChange" | "id">) {
  const errorId = `${id}-error`;
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        aria-required="true"
        onChange={(event) => onChange(event.target.value)}
        {...props}
      />
      {error ? (
        <p id={errorId} className="text-[16px] text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function SelectField({
  id,
  label,
  value,
  error,
  placeholder,
  options,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  error?: string;
  placeholder: string;
  options: readonly { value: string; label: string }[];
  onChange: (value: string) => void;
}) {
  const errorId = `${id}-error`;
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <select
        id={id}
        value={value}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        aria-required="true"
        className="h-11 w-full rounded-[6px] border border-line bg-paper px-3 text-[16px] text-ink"
        onChange={(event) => onChange(event.target.value)}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error ? (
        <p id={errorId} className="text-[16px] text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function ConsentCheck({
  id,
  checked,
  error,
  onCheckedChange,
  children,
}: {
  id: string;
  checked: boolean;
  error?: string;
  onCheckedChange: (checked: boolean) => void;
  children: ReactNode;
}) {
  const errorId = `${id}-error`;
  return (
    <div>
      <div className="flex items-start gap-3">
        <Checkbox
          id={id}
          checked={checked}
          onCheckedChange={(value) => onCheckedChange(value === true)}
          aria-required="true"
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
        />
        <Label htmlFor={id} className="cursor-pointer">
          {children}
        </Label>
      </div>
      {error ? (
        <p id={errorId} className="mt-2 text-[16px] text-danger">
          {error}
        </p>
      ) : null}
    </div>
  );
}
