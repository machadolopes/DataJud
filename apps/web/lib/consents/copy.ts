import type { ConsentsConfig } from "@/lib/config";

export type BookxpressCopy = {
  versionId: string;
  label: string;
  details: string;
  relationship: ConsentsConfig["bookxpress"]["relationship"];
  legalName: string;
  cnpj: string;
  contactEmail: string;
  proofRetentionYears: number;
};

export function currentBookxpressCopy(consents: ConsentsConfig): BookxpressCopy {
  const bookxpress = consents.bookxpress;
  const version = bookxpress.versions[bookxpress.currentVersion];
  if (!version) {
    throw new Error(
      `Consent version "${bookxpress.currentVersion}" is missing from config/consents.json.`,
    );
  }
  return {
    versionId: bookxpress.currentVersion,
    label: version.label,
    details: version.details,
    relationship: bookxpress.relationship,
    legalName: bookxpress.legalName,
    cnpj: bookxpress.cnpj,
    contactEmail: bookxpress.contactEmail,
    proofRetentionYears: bookxpress.proofRetentionYears,
  };
}
