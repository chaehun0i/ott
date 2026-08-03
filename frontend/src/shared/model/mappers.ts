import { z } from "zod";
import type {
  ContentCardView,
  Locale,
  LocalizedValue,
  RuntimeConfig,
  SafeExternalDestination,
} from "./presentation";

const runtimeConfigSchema = z.object({
  apiBasePath: z.string().startsWith("/"),
  defaultLocale: z.enum(["ko", "en"]),
  release: z.string().min(1).max(100),
  supportedLocales: z.array(z.enum(["ko", "en"])).min(2),
});

const contentSchema = z.object({
  content_id: z.string().min(1),
  title: z.string().min(1),
  original_title: z.string().min(1).optional(),
  locale: z.enum(["ko", "en"]).optional(),
  status: z.enum(["new", "popular", "upcoming", "leaving"]).default("new"),
  providers: z.array(z.string().min(1)).default([]),
  poster_url: z.url().optional(),
  last_updated: z.iso.datetime(),
  stale: z.boolean().default(false),
});

const allowedProviderHosts: Readonly<Record<string, ReadonlySet<string>>> = {
  Netflix: new Set(["netflix.com", "www.netflix.com"]),
  DisneyPlus: new Set(["disneyplus.com", "www.disneyplus.com"]),
  Wavve: new Set(["wavve.com", "www.wavve.com"]),
  Tving: new Set(["tving.com", "www.tving.com"]),
};

export function parseRuntimeConfig(input: unknown): RuntimeConfig {
  return runtimeConfigSchema.parse(input);
}

export function localizedValue(
  values: Partial<Record<Locale | "original", string>>,
  locale: Locale,
): LocalizedValue {
  const selected = values[locale];
  if (selected) return { fallback: false, locale, text: selected };
  const original = values.original;
  if (original) return { fallback: true, locale: "original", text: original };
  const fallbackLocale: Locale = locale === "ko" ? "en" : "ko";
  const fallback = values[fallbackLocale];
  if (fallback) return { fallback: true, locale: fallbackLocale, text: fallback };
  throw new Error("No localized value is available");
}

export function safeExternalDestination(
  provider: string,
  rawUrl: string | undefined,
  serverValidated: boolean,
): SafeExternalDestination | undefined {
  if (!rawUrl || !serverValidated) return undefined;
  try {
    const url = new URL(rawUrl);
    const hosts = allowedProviderHosts[provider];
    if (url.protocol !== "https:" || !hosts?.has(url.hostname)) return undefined;
    return { href: url.toString(), provider };
  } catch {
    return undefined;
  }
}

export function mapContentCard(input: unknown, locale: Locale): ContentCardView {
  const value = contentSchema.parse(input);
  return {
    contentId: value.content_id,
    freshness: { lastUpdated: value.last_updated, stale: value.stale },
    ...(value.poster_url ? { posterUrl: value.poster_url } : {}),
    providers: value.providers,
    status: value.status,
    title: localizedValue(
      {
        ...(value.locale ? { [value.locale]: value.title } : {}),
        ...(value.original_title ? { original: value.original_title } : {}),
      },
      locale,
    ),
  };
}
