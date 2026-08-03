import { expect, test } from "@playwright/test";

test("Feed to Detail to Back preserves the feed", async ({ page }) => {
  await page.goto("/feed");
  await page.getByRole("link", { name: "퇴근길 웃음" }).click();
  await expect(page.getByRole("heading", { name: "퇴근길 웃음" })).toBeVisible();
  await page.getByRole("button", { name: "피드로 돌아가기" }).click();
  await expect(page.getByRole("heading", { name: "OTT 최신 콘텐츠 통합 피드" })).toBeVisible();
});

test("Search and recommendation announce results", async ({ page }) => {
  await page.goto("/search");
  await page.getByRole("textbox", { name: "제목이나 조건" }).fill("코미디");
  await page.getByRole("button", { name: "검색" }).click();
  await expect(page.getByText("“코미디” 조건으로 2개 결과")).toBeVisible();
  await page.goto("/recommend");
  await page.getByRole("textbox", { name: "보고 싶은 콘텐츠" }).fill("퇴근 후 가벼운 코미디");
  await page.getByRole("button", { name: "추천받기" }).click();
  await expect(page.getByText("1시간 이내의 밝은 코미디 2편을 추천했어요.")).toBeVisible();
});

test("consent withdrawal and admin denial are explicit", async ({ page }) => {
  await page.goto("/account");
  await page.getByRole("button", { name: "개인화 동의 철회" }).click();
  await expect(page.getByText("개인화 동의를 철회하고 추천 데이터를 삭제했습니다.")).toBeVisible();
  await page.goto("/admin");
  await expect(page.getByRole("alert")).toContainText("접근 권한이 없습니다");
});

test("keyboard navigation and 200 percent zoom reflow", async ({ page }, testInfo) => {
  await page.goto("/feed");
  if (testInfo.project.name === "webkit")
    await page.getByRole("link", { name: "본문으로 건너뛰기" }).focus();
  else await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "본문으로 건너뛰기" })).toBeFocused();
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow).toBe(false);
});

test("core web vital and request budgets are measured", async ({ page }) => {
  await page.addInitScript(() => {
    const values: Record<string, number> = { cls: 0 };
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) values.lcp = entry.startTime;
    }).observe({ type: "largest-contentful-paint", buffered: true });
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const shift = entry as PerformanceEntry & { hadRecentInput?: boolean; value?: number };
        if (!shift.hadRecentInput) values.cls = (values.cls ?? 0) + (shift.value ?? 0);
      }
    }).observe({ type: "layout-shift", buffered: true });
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const event = entry as PerformanceEntry & { duration: number };
        values.inp = Math.max(values.inp ?? 0, event.duration);
      }
    }).observe({ type: "event", buffered: true, durationThreshold: 16 });
    Object.defineProperty(window, "__webVitals", { value: values });
  });
  await page.goto("/feed");
  await page.getByRole("combobox", { name: "장르" }).selectOption("코미디");
  const result = await page.evaluate(() => ({
    metrics: (window as Window & { __webVitals: Record<string, number> }).__webVitals,
    requests: performance.getEntriesByType("resource").length,
  }));
  expect(result.requests).toBeLessThanOrEqual(25);
  expect(result.metrics.cls).toBeLessThanOrEqual(0.1);
  if (result.metrics.lcp !== undefined) expect(result.metrics.lcp).toBeLessThan(2500);
  if (result.metrics.inp !== undefined) expect(result.metrics.inp).toBeLessThan(200);
});

test("automated axe scan has no serious violations", async ({ page }) => {
  await page.goto("/feed");
  await page.addScriptTag({ path: "node_modules/axe-core/axe.min.js" });
  const violations = await page.evaluate(async () => {
    const axe = (
      window as Window & {
        axe: { run: () => Promise<{ violations: { impact: string | null }[] }> };
      }
    ).axe;
    return (await axe.run()).violations.filter(
      (item) => item.impact === "serious" || item.impact === "critical",
    );
  });
  expect(violations).toEqual([]);
});
