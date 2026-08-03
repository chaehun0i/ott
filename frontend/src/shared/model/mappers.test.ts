import {
  localizedValue,
  mapContentCard,
  parseRuntimeConfig,
  safeExternalDestination,
} from "./mappers";

it("rejects unsafe external destinations", () => {
  expect(safeExternalDestination("Netflix", "javascript:alert(1)", true)).toBeUndefined();
  expect(safeExternalDestination("Netflix", "https://evil.example/title", true)).toBeUndefined();
  expect(
    safeExternalDestination("Netflix", "https://www.netflix.com/title", false),
  ).toBeUndefined();
});

it("accepts a validated provider destination", () => {
  expect(safeExternalDestination("Netflix", "https://www.netflix.com/title", true)).toEqual({
    href: "https://www.netflix.com/title",
    provider: "Netflix",
  });
});

it("uses original title before alternate locale", () => {
  expect(localizedValue({ original: "Original", en: "English" }, "ko")).toEqual({
    fallback: true,
    locale: "original",
    text: "Original",
  });
});

it("maps validated transport content without inventing fields", () => {
  const card = mapContentCard(
    {
      content_id: "content-1",
      title: "작품",
      locale: "ko",
      providers: ["Netflix"],
      last_updated: "2026-08-03T00:00:00Z",
    },
    "ko",
  );
  expect(card.contentId).toBe("content-1");
  expect(card.posterUrl).toBeUndefined();
  expect(card.title.text).toBe("작품");
});

it("validates public runtime configuration", () => {
  expect(
    parseRuntimeConfig({
      apiBasePath: "/api/v1",
      defaultLocale: "ko",
      supportedLocales: ["ko", "en"],
      release: "test",
    }),
  ).toMatchObject({ defaultLocale: "ko" });
});
