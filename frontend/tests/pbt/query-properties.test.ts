import fc from "fast-check";
import { localizedValue } from "@/shared/model/mappers";
import { normalizeFeedQuery, parseFeedQuery, serializeFeedQuery } from "@/shared/query/feed-query";
import { feedQueryArbitrary, localizedMapArbitrary } from "./strategies";

describe("P-U01-01~04 query and locale properties", () => {
  it("P-U01-01 round-trips canonical feed queries", () => {
    fc.assert(
      fc.property(feedQueryArbitrary, (query) => {
        expect(parseFeedQuery(serializeFeedQuery(query))).toEqual(normalizeFeedQuery(query));
      }),
    );
  });

  it("P-U01-02 normalization is idempotent", () => {
    fc.assert(
      fc.property(feedQueryArbitrary, (query) => {
        expect(normalizeFeedQuery(normalizeFeedQuery(query))).toEqual(normalizeFeedQuery(query));
      }),
    );
  });

  it("P-U01-03 filter insertion order is commutative", () => {
    fc.assert(
      fc.property(feedQueryArbitrary, (query) => {
        const reversed = {
          ...query,
          genres: [...query.genres].reverse(),
          ott: [...query.ott].reverse(),
        };
        expect(serializeFeedQuery(reversed)).toBe(serializeFeedQuery(query));
      }),
    );
  });

  it("P-U01-04 selects the first available locale value", () => {
    fc.assert(
      fc.property(
        localizedMapArbitrary,
        fc.constantFrom("ko" as const, "en" as const),
        (map, locale) => {
          fc.pre(Boolean(map[locale] ?? map.original ?? map[locale === "ko" ? "en" : "ko"]));
          const expected = map[locale] ?? map.original ?? map[locale === "ko" ? "en" : "ko"];
          expect(localizedValue(map, locale).text).toBe(expected);
        },
      ),
    );
  });
});
