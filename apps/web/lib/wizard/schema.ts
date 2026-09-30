import { z } from "zod";
import { isValidCpf } from "@/lib/cpf";

export const genreValues = [
  "romance",
  "novela",
  "contos",
  "fantasia",
  "ficcao-cientifica",
  "suspense-policial",
  "terror",
  "romance-historico",
  "jovem-adulto",
  "outro",
] as const;

export const audienceValues = ["adulto", "jovem-adulto", "infantojuvenil"] as const;

export const genreOptions: { value: (typeof genreValues)[number]; label: string }[] = [
  { value: "romance", label: "Romance" },
  { value: "novela", label: "Novela" },
  { value: "contos", label: "Contos" },
  { value: "fantasia", label: "Fantasia" },
  { value: "ficcao-cientifica", label: "Ficção científica" },
  { value: "suspense-policial", label: "Suspense/policial" },
  { value: "terror", label: "Terror" },
  { value: "romance-historico", label: "Romance histórico" },
  { value: "jovem-adulto", label: "Jovem adulto" },
  { value: "outro", label: "Outro" },
];

export const audienceOptions: { value: (typeof audienceValues)[number]; label: string }[] = [
  { value: "adulto", label: "Adulto" },
  { value: "jovem-adulto", label: "Jovem adulto" },
  { value: "infantojuvenil", label: "Infantojuvenil" },
];

export const workSchema = z
  .object({
    name: z.string().trim().min(2, "Informe seu nome."),
    email: z.string().trim().email("Informe um e-mail válido."),
    emailConfirm: z.string().trim().email("Confirme o e-mail."),
    cpf: z.string().refine(isValidCpf, "Informe um CPF válido."),
    title: z.string().trim().min(1, "Informe o título da obra."),
    genre: z.enum(genreValues, { errorMap: () => ({ message: "Escolha o gênero." }) }),
    audience: z.enum(audienceValues, {
      errorMap: () => ({ message: "Escolha o público-alvo." }),
    }),
    acceptTerms: z.boolean().refine((value) => value, "Aceite os termos para continuar."),
    acceptAi: z
      .boolean()
      .refine((value) => value, "É preciso estar ciente do uso de inteligência artificial."),
    bookxpressOptIn: z.boolean(),
  })
  .refine((value) => value.email.toLowerCase() === value.emailConfirm.toLowerCase(), {
    message: "Os e-mails não coincidem.",
    path: ["emailConfirm"],
  });

export type WorkFormValues = z.infer<typeof workSchema>;

export function emptyWorkForm(): {
  name: string;
  email: string;
  emailConfirm: string;
  cpf: string;
  title: string;
  genre: string;
  audience: string;
  acceptTerms: boolean;
  acceptAi: boolean;
  bookxpressOptIn: boolean;
} {
  return {
    name: "",
    email: "",
    emailConfirm: "",
    cpf: "",
    title: "",
    genre: "",
    audience: "",
    acceptTerms: false,
    acceptAi: false,
    bookxpressOptIn: false,
  };
}

export function fieldErrors(error: z.ZodError): Record<string, string> {
  const errors: Record<string, string> = {};
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (typeof key === "string" && !errors[key]) {
      errors[key] = issue.message;
    }
  }
  return errors;
}
