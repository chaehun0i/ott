export interface FeedQuery {
  cursor?: string;
  genres: string[];
  locale: "ko" | "en";
  ott: string[];
  sort: "latest" | "popular";
}

function uniqueSorted(values: Iterable<string>): string[] {
  return [...new Set([...values].map((value) => value.trim()).filter(Boolean))].sort((a, b) =>
    a.localeCompare(b),
  );
}

export function normalizeFeedQuery(query: FeedQuery): FeedQuery {
  return {
    ...(query.cursor?.trim() ? { cursor: query.cursor.trim() } : {}),
    genres: uniqueSorted(query.genres),
    locale: query.locale === "en" ? "en" : "ko",
    ott: uniqueSorted(query.ott),
    sort: query.sort === "popular" ? "popular" : "latest",
  };
}

export function serializeFeedQuery(query: FeedQuery): string {
  const normalized = normalizeFeedQuery(query);
  const params = new URLSearchParams();
  for (const genre of normalized.genres) params.append("genre", genre);
  for (const ott of normalized.ott) params.append("ott", ott);
  params.set("locale", normalized.locale);
  params.set("sort", normalized.sort);
  if (normalized.cursor) params.set("cursor", normalized.cursor);
  return params.toString();
}

export function parseFeedQuery(raw: string): FeedQuery {
  const params = new URLSearchParams(raw.startsWith("?") ? raw.slice(1) : raw);
  return normalizeFeedQuery({
    ...(params.get("cursor") ? { cursor: params.get("cursor") ?? undefined } : {}),
    genres: params.getAll("genre"),
    locale: params.get("locale") === "en" ? "en" : "ko",
    ott: params.getAll("ott"),
    sort: params.get("sort") === "popular" ? "popular" : "latest",
  });
}
