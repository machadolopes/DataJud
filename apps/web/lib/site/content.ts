import { cache } from "react";
import { currentBookxpressCopy } from "@/lib/consents/copy";
import {
  loadConsents,
  loadLimits,
  loadPricing,
  loadRetention,
  loadSeller,
  maxUploadMb,
} from "@/lib/config";

export const loadSiteContent = cache(function loadSiteContent() {
  const pricing = loadPricing();
  const seller = loadSeller().seller;
  const limits = loadLimits();
  const retention = loadRetention();
  const bookxpress = currentBookxpressCopy(loadConsents());
  return {
    pricing,
    seller,
    limits,
    retention,
    bookxpress,
    maxUploadMb: maxUploadMb(),
    pricesUnpublished: pricing.tiers.some((tier) => tier.priceCents === 0),
  };
});

export type SiteContent = ReturnType<typeof loadSiteContent>;
