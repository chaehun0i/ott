import fc from "fast-check";
import type { FeedQuery } from "@/shared/query/feed-query";

const label = fc
  .string({
    minLength: 1,
    maxLength: 24,
    unit: fc.constantFrom(
      "a",
      "b",
      "c",
      "A",
      "B",
      "C",
      "0",
      "1",
      "2",
      " ",
      "가",
      "나",
      "다",
      "라",
      "마",
    ),
  })
  .filter((value) => value.trim().length > 0);

export const feedQueryArbitrary: fc.Arbitrary<FeedQuery> = fc.record({
  cursor: fc.option(label, { nil: undefined }),
  genres: fc.array(label, { maxLength: 6 }),
  locale: fc.constantFrom("ko" as const, "en" as const),
  ott: fc.array(label, { maxLength: 6 }),
  sort: fc.constantFrom("latest" as const, "popular" as const),
});

export const localizedMapArbitrary = fc.record(
  {
    ko: label,
    en: label,
    original: label,
  },
  { requiredKeys: [] },
);
