export type Locale = "ko" | "en";
export type ResourceStatus =
  "idle" | "pending" | "success" | "empty" | "stale" | "degraded" | "error";

export interface LocalizedValue {
  fallback: boolean;
  locale: Locale | "original";
  text: string;
}

export interface AvailabilityView {
  available: boolean;
  destination?: SafeExternalDestination;
  provider: string;
  region: string;
}

export interface SafeExternalDestination {
  href: string;
  provider: string;
}

export interface ContentCardView {
  contentId: string;
  freshness: { lastUpdated: string; stale: boolean };
  posterUrl?: string;
  providers: string[];
  status: "new" | "popular" | "upcoming" | "leaving";
  title: LocalizedValue;
}

export interface RecommendationCardView extends ContentCardView {
  evidence: ReadonlyArray<{ field: string; source: string; value: string }>;
  reason: string;
  summary: string;
}

export interface SessionView {
  authenticated: boolean;
  roles: ReadonlyArray<"member" | "operator" | "administrator">;
}

export interface ConsentView {
  effectiveAt: string;
  purpose: "personalization" | "analytics" | "notification";
  status: "granted" | "withdrawn";
}

export interface RemoteResource<T> {
  data?: T;
  fetchedAt?: string;
  reason?: string;
  status: ResourceStatus;
}

export interface RuntimeConfig {
  apiBasePath: string;
  defaultLocale: Locale;
  release: string;
  supportedLocales: Locale[];
}
